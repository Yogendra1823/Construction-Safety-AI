"""
AI Recommendation Engine — scans a project's materials, budget and schedule
signals and queries Ollama (Gemma3:1b) to produce short, actionable recommendations.
"""
from ai_engine import llm_client

def generate_recommendations(project, materials, budget_items, delay_level, delay_risk):
    if not llm_client.is_available():
        return [{
            "category": "System Error",
            "impact": "High",
            "message": "Ollama is currently offline. Start the Ollama server to view AI recommendations."
        }]

    # Build the prompt payload based on the live data
    data_context = (
        f"Project: {project.name}, Progress: {project.progress_percent:.0f}%, Status: {project.status}\n"
        f"Delay Risk Level: {delay_level} (Score: {delay_risk}/100)\n\n"
        "Materials:\n"
    )
    for m in materials:
        data_context += f"- {m.material_name}: {m.availability} ({m.usage_pct}% used)\n"

    data_context += "\nBudget:\n"
    for b in budget_items:
        spent_pct = (b.spent_amount / b.allocated_amount * 100) if b.allocated_amount else 0
        data_context += f"- {b.category}: {spent_pct:.0f}% spent\n"

    system_prompt = (
        "You are an expert Construction Manager AI. Review the project data below and generate exactly 3 highly actionable recommendations. "
        "For each recommendation, you MUST provide it exactly in this text format:\n"
        "CATEGORY: [Material Purchase OR Budget Savings OR Timeline Improvements OR Resource Allocation]\n"
        "IMPACT: [High OR Medium OR Low]\n"
        "MESSAGE: [One concise, professional sentence explaining the recommendation]\n\n"
        "Do not include any other text, greetings, or markdown formatting."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": data_context}
    ]

    try:
        # Generate the response (streaming generator -> string)
        response_gen = llm_client.chat_stream(messages)
        full_text = "".join(list(response_gen))
        
        # Parse the custom text format safely
        recs = []
        current_rec = {}
        for line in full_text.split('\n'):
            line = line.strip()
            if line.upper().startswith("CATEGORY:"):
                if current_rec: recs.append(current_rec)
                current_rec = {"category": line[9:].strip()}
            elif line.upper().startswith("IMPACT:"):
                current_rec["impact"] = line[7:].strip().capitalize()
                if current_rec["impact"] not in ["High", "Medium", "Low"]:
                    current_rec["impact"] = "Medium"
            elif line.upper().startswith("MESSAGE:"):
                current_rec["message"] = line[8:].strip()
                
        if current_rec:
            recs.append(current_rec)
            
        # Ensure fallback if parsing fails completely
        if not recs:
            recs.append({
                "category": "General Advice",
                "impact": "Medium",
                "message": "Continue monitoring project milestones and ensure material stocks are replenished before they run out."
            })
            
        return recs
        
    except Exception as e:
        return [{
            "category": "System Error",
            "impact": "High",
            "message": f"AI Generation failed: {str(e)}"
        }]
