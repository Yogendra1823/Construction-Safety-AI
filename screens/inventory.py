from datetime import date, timedelta

import pandas as pd
import streamlit as st

from database.db import session_scope
from database.models import InventoryItem, PurchaseOrder, Project
from utils.styling import section_header, kpi_card, status_badge, card_open, card_close


def render():
    section_header("Inventory", "Warehouse stock levels and purchase orders")

    with session_scope() as db:
        items = db.query(InventoryItem).all()
        orders = db.query(PurchaseOrder).order_by(PurchaseOrder.order_date.desc()).all()
        projects = {p.id: p for p in db.query(Project).all()}

        low_stock = [i for i in items if i.quantity_in_stock <= i.reorder_level]
        pending_orders = [o for o in orders if o.status == "Pending"]

        c1, c2, c3 = st.columns(3)
        with c1: kpi_card("Stock Items", len(items), "📦", accent="primary")
        with c2: kpi_card("Below Reorder Level", len(low_stock), "⚠️", accent="danger" if low_stock else "success")
        with c3: kpi_card("Pending Purchase Orders", len(pending_orders), "🚚", accent="warning" if pending_orders else "success")

        st.write("")
        with st.container(border=True):
            section_header("Warehouse Stock")
            if items:
                df = pd.DataFrame([{
                    "Item": i.item_name, "Category": i.category, "In Stock": i.quantity_in_stock, "Unit": i.unit,
                    "Reorder Level": i.reorder_level, "Warehouse": i.warehouse_location,
                    "Status": "Reorder Now" if i.quantity_in_stock <= i.reorder_level else "OK",
                } for i in items])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.caption("No inventory items recorded yet.")
            with st.form("add_inventory", clear_on_submit=True):
                c1, c2, c3, c4 = st.columns(4)
                name = c1.text_input("Item name")
                cat = c2.text_input("Category")
                qty = c3.number_input("Quantity", min_value=0.0, value=100.0)
                reorder = c4.number_input("Reorder level", min_value=0.0, value=20.0)
                unit = st.text_input("Unit", value="units")
                if st.form_submit_button("Add Item"):
                    if name:
                        db.add(InventoryItem(item_name=name, category=cat, quantity_in_stock=qty, unit=unit,
                                              reorder_level=reorder, warehouse_location="Warehouse A"))
                        st.rerun()

        st.write("")
        with st.container(border=True):
            section_header("Purchase Orders")
            if orders:
                df_o = pd.DataFrame([{
                    "Supplier": o.supplier_name, "Item": o.item_name, "Qty": o.quantity,
                    "Unit Cost (₹)": o.unit_cost, "Project": projects.get(o.project_id).name if o.project_id in projects else "General Stock",
                    "Order Date": o.order_date, "Expected Delivery": o.expected_delivery, "Status": o.status,
                } for o in orders])
                st.dataframe(df_o, use_container_width=True, hide_index=True)
            with st.form("add_po", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                supplier = c1.text_input("Supplier")
                item = c2.text_input("Item")
                qty = c3.number_input("Quantity", min_value=0.0, value=500.0)
                c4, c5 = st.columns(2)
                cost = c4.number_input("Unit cost (₹)", min_value=0.0, value=100.0)
                delivery = c5.date_input("Expected delivery", value=date.today() + timedelta(days=7))
                if st.form_submit_button("Create Purchase Order", type="primary"):
                    if supplier and item:
                        db.add(PurchaseOrder(supplier_name=supplier, item_name=item, quantity=qty, unit_cost=cost,
                                              order_date=date.today(), expected_delivery=delivery, status="Pending"))
                        st.rerun()
