"""
Shared chat rendering, used in two places:
  1. The AI Assistant page's full "Chat" tab
  2. The floating chat widget (bottom-right, visible on every other page)

Both read/write the same st.session_state["chat_history"], so a conversation
started in one place continues seamlessly in the other.
"""
import streamlit as st

from ai_engine.chatbot import answer_question
from ai_engine import llm_client
from config import OLLAMA_MODEL
from utils.styling import status_badge


def render_chat_ui(key_prefix: str, project_id: int = None, height: int = None):
    if key_prefix == "floating":
        st.markdown(
            """
            <div style="margin: -1rem -1rem 1rem -1rem; padding: 1rem 1.2rem; background: rgba(14, 17, 23, 0.8); border-bottom: 1px solid rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: space-between; position: sticky; top: -1rem; z-index: 100; backdrop-filter: blur(12px);">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 38px; height: 38px; border-radius: 10px; background: linear-gradient(135deg, #0A84FF, #0050A0); display: flex; align-items: center; justify-content: center; font-size: 1.2rem; box-shadow: 0 4px 10px rgba(10,132,255,0.3);">💬</div>
                    <div>
                        <div style="font-weight: 700; font-family: 'Space Grotesk', sans-serif; font-size: 1.05rem; color: #fff; letter-spacing: -0.01em;">CI Hub AI Assistant</div>
                        <div style="font-size: 0.75rem; color: rgba(255,255,255,0.6); display: flex; align-items: center; gap: 6px; margin-top: 2px;">
                            <div style="width: 6px; height: 6px; border-radius: 50%; background: #28a745; box-shadow: 0 0 6px #28a745;"></div> Online (Gemma3:1b)
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True
        )

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    history = st.session_state["chat_history"]
    history_box = st.container(height=height) if height else st.container()
    with history_box:
        if not history:
            st.caption('Try: "Project status?" · "Remaining budget?" · "Cement required?" · "Delayed projects?" · "Workers today?"')
        for role, msg, source in history:
            with st.chat_message(role):
                st.write(msg)
                if source == "llm":
                    st.caption(f"— {OLLAMA_MODEL} (local)")

        # Container for new messages, positioned strictly BEFORE chat_input in the DOM
        new_msgs = st.container()

        prompt = st.chat_input("Ask about your projects...", key=f"chat_input_{key_prefix}")
        
    if prompt:
        # Snapshot history before modification to pass a stable, non-mutable context
        history_snapshot = list(st.session_state["chat_history"])

        st.session_state["chat_history"].append(("user", prompt, None))
        
        # Pre-append assistant placeholder
        st.session_state["chat_history"].append(("assistant", "", "llm"))
        history_idx = len(st.session_state["chat_history"]) - 1
        
        with new_msgs:
            with st.chat_message("user"):
                st.write(prompt)
                
            with st.chat_message("assistant"):
                try:
                    answer, source = answer_question(prompt, project_id=project_id, chat_history=history_snapshot)
                    
                    if hasattr(answer, '__iter__') and not isinstance(answer, str):
                        with st.spinner("AI is thinking..."):
                            try:
                                first_chunk = next(answer)
                            except StopIteration:
                                first_chunk = ""
                        
                        # Capture first_chunk in a local variable for the closure
                        _first = first_chunk
                        _rest = answer
                        
                        def combined_stream(_f=_first, _r=_rest):
                            accumulated = ""
                            if _f:
                                accumulated += _f
                                st.session_state["chat_history"][history_idx] = ("assistant", accumulated, source)
                                yield _f
                            for chunk in _r:
                                accumulated += chunk
                                st.session_state["chat_history"][history_idx] = ("assistant", accumulated, source)
                                yield chunk
                                
                        final_text = st.write_stream(combined_stream())
                        st.session_state["chat_history"][history_idx] = ("assistant", final_text, source)
                    else:
                        st.write(answer)
                        st.session_state["chat_history"][history_idx] = ("assistant", answer, source)
                        
                    if source == "llm":
                        st.caption(f"— {OLLAMA_MODEL} (local)")
                        
                except Exception as e:
                    # Remove the orphaned placeholder if the LLM call fails
                    if history_idx < len(st.session_state["chat_history"]):
                        st.session_state["chat_history"].pop(history_idx)
                    st.error(f"AI Assistant temporarily unavailable. Please try again. ({type(e).__name__})")
        
        # Rerun the page to reset state, EXCEPT for the floating chat (which would collapse on rerun)
        if key_prefix != "floating":
            st.rerun()
