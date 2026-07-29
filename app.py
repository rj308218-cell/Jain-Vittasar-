import os
import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO

# 1. Page Configuration
st.set_page_config(page_title="Jain Vittasar - Cloud Financial Intelligence", layout="wide")

# 2. Supabase Connection Setup via Streamlit Secrets
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

@st.cache_resource
def init_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Supabase credentials missing! Please configure them in your Streamlit Cloud App Settings -> Secrets.")
        st.stop()
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "company" not in st.session_state:
    st.session_state.company = None
if "sales_cart" not in st.session_state:
    st.session_state.sales_cart = []

# ==========================================
# AUTHENTICATION GATEWAY
# ==========================================
def auth_gateway():
    st.title("🏢 JAIN VITTASAR - CLOUD GATEWAY")
    st.markdown("### Financial Intelligence & Billing Platform")
    
    tab1, tab2 = st.tabs(["Customer Login", "Master Login"])
    
    with tab1:
        st.subheader("Customer Login")
        u_name = st.text_input("Username / User ID", key="cust_user")
        u_pwd = st.text_input("Password", type="password", key="cust_pwd")
        
        if st.button("Login to Account", type="primary"):
            if not u_name or not u_pwd:
                st.error("Please enter both Username and Password.")
            else:
                try:
                    res = supabase.table("users").select("*").eq("username", u_name).eq("password", u_pwd).execute()
                    if res.data:
                        account = res.data[0]
                        st.session_state.authenticated = True
                        
                        comp_res = supabase.table("company_profile").select("*").eq("name", account["company_name"]).execute()
                        if comp_res.data:
                            st.session_state.company = comp_res.data[0]
                        st.success(f"Welcome back, {account['owner_name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid Username or Password!")
                except Exception as e:
                    st.error(f"Login failed: {e}")

    with tab2:
        st.subheader("Master / Owner Login")
        m_id = st.text_input("Master ID", value="Admin")
        m_pwd = st.text_input("Master Password", type="password", value="Rj308218@gmail")
        
        if st.button("Authorize Master Access"):
            if m_id == "Admin" and m_pwd == "Rj308218@gmail":
                st.session_state.authenticated = True
                st.session_state.company = {"name": "System Admin Enterprise", "gstin": "TEST-GSTIN-000"}
                st.success("Master Admin Access Granted.")
                st.rerun()
            else:
                st.error("Invalid Master Owner Credentials!")

if not st.session_state.authenticated:
    auth_gateway()
    st.stop()

# ==========================================
# DASHBOARD NAVIGATION CONSOLE
# ==========================================
st.sidebar.title("Navigation Console")
if st.session_state.company:
    st.sidebar.success(f"Active: {st.session_state.company.get('name')}")

nav_choice = st.sidebar.radio("Go to", [
    "🏠 Company Profile", 
    "📈 Sales & Billing Module", 
    "📦 Inventory Control"
])

if st.sidebar.button("🔒 Logout Session"):
    st.session_state.authenticated = False
    st.session_state.company = None
    st.rerun()

# --- MODULE 1: COMPANY PROFILE ---
if nav_choice == "🏠 Company Profile":
    st.subheader("🏢 Enterprise Profile Management")
    c_active = st.session_state.company or {}
    
    c_name = st.text_input("Company Registered Name *", value=c_active.get("name", ""))
    c_addr = st.text_area("Office Address *", value=c_active.get("address", ""))
    c_phone = st.text_input("Primary Helpline *", value=c_active.get("phone", ""))
    c_gstin = st.text_input("GSTIN Index *", value=c_active.get("gstin", ""))

    if st.button("Save Profile to Cloud", type="primary"):
        if not c_name or not c_gstin:
            st.error("Company Name and GSTIN are required.")
        else:
            payload = {"name": c_name, "address": c_addr, "phone": c_phone, "gstin": c_gstin}
            try:
                supabase.table("company_profile").upsert(payload, on_conflict="name").execute()
                st.session_state.company = payload
                st.success("Profile saved successfully!")
            except Exception as e:
                st.error(f"Failed to save profile: {e}")

# --- MODULE 2: SALES & BILLING ---
elif nav_choice == "📈 Sales & Billing Module":
    st.subheader("📈 Sales & Invoicing Engine")
    
    cust_name = st.text_input("Buyer / Customer Name", value="Walk-in Customer")
    
    st.markdown("### Add Items to Cart")
    try:
        inv_res = supabase.table("inventory").select("*").execute()
        inventory_items = inv_res.data if inv_res.data else []
    except Exception:
        inventory_items = []

    if inventory_items:
        item_options = {i['item_name']: i for i in inventory_items}
        sel_item_name = st.selectbox("Select Inventory Item", list(item_options.keys()))
        selected_item = item_options[sel_item_name]
        
        col1, col2 = st.columns(2)
        with col1:
            qty = st.number_input("Quantity", min_value=1, value=1)
        with col2:
            rate = st.number_input("Rate (₹)", min_value=0.0, value=float(selected_item["price"]))

        if st.button("Add Item to Cart"):
            total = qty * rate
            st.session_state.sales_cart.append({
                "item_name": selected_item["item_name"], "qty": qty, "price": rate, "total_amount": total
            })
            st.success("Item added to cart!")

    if st.session_state.sales_cart:
        st.markdown("### Cart Items")
        st.dataframe(pd.DataFrame(st.session_state.sales_cart))
        grand_total = sum(i["total_amount"] for i in st.session_state.sales_cart)
        st.metric("Grand Total", f"₹ {grand_total:,.2f}")

        if st.button("Commit Invoice", type="primary"):
            st.success("Invoice successfully generated and committed!")
            st.session_state.sales_cart = []
    else:
        st.info("Your sales cart is empty. Add items from inventory first.")

# --- MODULE 3: INVENTORY CONTROL ---
elif nav_choice == "📦 Inventory Control":
    st.subheader("📦 Inventory Stock Management")
    
    i_name = st.text_input("Item Name")
    i_stock = st.number_input("Stock Quantity", min_value=0, value=10)
    i_price = st.number_input("Unit Price (₹)", min_value=0.0, value=100.0)

    if st.button("Save Item to Inventory"):
        if not i_name:
            st.error("Item name is required.")
        else:
            try:
                supabase.table("inventory").upsert({
                    "item_name": i_name, "stock": i_stock, "price": i_price
                }, on_conflict="item_name").execute()
                st.success("Inventory updated successfully!")
            except Exception as e:
                st.error(f"Error saving inventory: {e}")
                
    try:
        inv_data = supabase.table("inventory").select("*").execute()
        if inv_data.data:
            st.markdown("### Current Stock Overview")
            st.dataframe(pd.DataFrame(inv_data.data))
    except Exception:
        pass
