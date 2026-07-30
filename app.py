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
from num2words import num2words

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
# AUTHENTICATION & SIGNUP GATEWAY
# ==========================================
# ==========================================
# AUTHENTICATION & SIGNUP GATEWAY
# ==========================================
def auth_gateway():
    st.title("🏢 JAIN VITTASAR - CLOUD GATEWAY")
    st.markdown("### Financial Intelligence & Billing Platform")
    
    tab1, tab2, tab3 = st.tabs(["Customer Login", "Master Login", "New Registration & Signup"])
    
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

    with tab3:
        st.subheader("New Business Registration & Subscription")
        reg_biz = st.text_input("Business Name *", key="reg_biz")
        reg_owner = st.text_input("Owner Full Name *", key="reg_owner")
        reg_email = st.text_input("Email Address *", key="reg_email")
        reg_mobile = st.text_input("Mobile Number *", key="reg_mobile")
        reg_addr = st.text_area("Office Address *", key="reg_addr")
        
        # Optional GSTIN Checkbox Flow
        has_gstin = st.checkbox("Do you have a GSTIN?", key="reg_has_gstin")
        reg_gstin = ""
        if has_gstin:
            reg_gstin = st.text_input("GSTIN Number", key="reg_gstin")
        
        st.markdown("---")
        plan_choice = st.selectbox("Select Subscription Plan", ["1 Day Plan (₹10)", "1 Month Plan (₹250)", "Custom Plan (90+ Days - 10% Off)"])
        
        reg_user = st.text_input("Create Username *", key="reg_user")
        reg_pwd = st.text_input("Create Password *", type="password", key="reg_pwd")

        if st.button("Complete Registration", type="primary"):
            if not reg_biz or not reg_owner or not reg_email or not reg_mobile or not reg_addr or not reg_user or not reg_pwd:
                st.error("Please fill out all required fields (*).")
            else:
                try:
                    # Check if username exists
                    check_user = supabase.table("users").select("id").eq("username", reg_user).execute()
                    if check_user.data:
                        st.error("Username already taken! Choose another.")
                    else:
                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Insert User (Storing email inside user payload or expanding if column exists)
                        user_payload = {
                            "company_name": reg_biz,
                            "owner_name": reg_owner,
                            "mobile": reg_mobile,
                            "address": reg_addr,
                            "gstin": reg_gstin if has_gstin else "",
                            "plan_name": plan_choice,
                            "plan_days": 1 if "1 Day" in plan_choice else 30,
                            "amount_paid": 10 if "1 Day" in plan_choice else 250,
                            "username": reg_user,
                            "password": reg_pwd,
                            "created_at": now_str
                        }
                        supabase.table("users").insert(user_payload).execute()

                        # Insert Company Profile
                        comp_payload = {
                            "name": reg_biz,
                            "address": reg_addr,
                            "phone": reg_mobile,
                            "gstin": reg_gstin if has_gstin else "Unregistered",
                            "financial_year": "2026-2027"
                        }
                        supabase.table("company_profile").upsert(comp_payload, on_conflict="name").execute()

                        st.success("Registration successful! You can now log in via the Customer Login tab.")
                except Exception as e:
                    st.error(f"Registration failed: {e}")

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
    "📦 Inventory Control",
    "👥 Parties & Customers Ledger",
    "📊 Invoices & Audit Logs"
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
    c_pan = st.text_input("PAN Number", value=c_active.get("pan", ""))
    c_bank = st.text_input("Bank Name", value=c_active.get("bank_name", ""))
    c_acc = st.text_input("Account Number", value=c_active.get("account_no", ""))
    c_ifsc = st.text_input("IFSC Code", value=c_active.get("ifsc", ""))

    if st.button("Save Profile to Cloud", type="primary"):
        if not c_name or not c_gstin:
            st.error("Company Name and GSTIN are required.")
        else:
            payload = {
                "name": c_name, "address": c_addr, "phone": c_phone, 
                "gstin": c_gstin, "pan": c_pan, "bank_name": c_bank, 
                "account_no": c_acc, "ifsc": c_ifsc
            }
            try:
                supabase.table("company_profile").upsert(payload, on_conflict="name").execute()
                st.session_state.company = payload
                st.success("Profile saved successfully!")
            except Exception as e:
                st.error(f"Failed to save profile: {e}")

# --- MODULE 2: SALES & BILLING ---
elif nav_choice == "📈 Sales & Billing Module":
    st.subheader("📈 Sales & Invoicing Engine")
    
    try:
        parties_res = supabase.table("parties").select("party_name").execute()
        party_list = ["Walk-in Customer"] + [p["party_name"] for p in parties_res.data] if parties_res.data else ["Walk-in Customer"]
    except Exception:
        party_list = ["Walk-in Customer"]

    cust_name = st.selectbox("Buyer / Customer Name", party_list)
    inv_type = st.selectbox("Invoice Classification", ["TAX Invoice", "PROFORMA Invoice"])
    
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
        
        col1, col2, col3 = st.columns(3)
        with col1:
            qty = st.number_input("Quantity", min_value=1, value=1)
        with col2:
            rate = st.number_input("Rate (₹)", min_value=0.0, value=float(selected_item["price"]))
        with col3:
            tax_rate = st.selectbox("Tax Rate (%)", [0, 5, 12, 18, 28], index=3)

        if st.button("Add Item to Cart"):
            base_total = qty * rate
            tax_amount = base_total * (tax_rate / 100.0)
            net_total = base_total + tax_amount
            
            st.session_state.sales_cart.append({
                "item_name": selected_item["item_name"], 
                "hsn_code": selected_item.get("hsn_code", ""),
                "qty": qty, 
                "price": rate, 
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "total_amount": net_total
            })
            st.success("Item added to cart!")

    if st.session_state.sales_cart:
        st.markdown("### Cart Items")
        st.dataframe(pd.DataFrame(st.session_state.sales_cart))
        
        grand_total = sum(i["total_amount"] for i in st.session_state.sales_cart)
        total_tax = sum(i["tax_amount"] for i in st.session_state.sales_cart)
        st.metric("Grand Total (Inc. Tax)", f"₹ {grand_total:,.2f}")

        def generate_pdf_invoice(bill_no, customer, items, g_total, t_tax):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            story = []
            styles = getSampleStyleSheet()
            
            comp = st.session_state.company or {}
            story.append(Paragraph(f"<b>{comp.get('name', 'Jain Vittasar Enterprise')}</b>", styles['Heading1']))
            story.append(Paragraph(f"Address: {comp.get('address', 'N/A')} | GSTIN: {comp.get('gstin', 'N/A')}", styles['Normal']))
            story.append(Spacer(1, 15))
            
            story.append(Paragraph(f"<b>Tax Invoice #{bill_no}</b>", styles['Heading2']))
            story.append(Paragraph(f"<b>Customer:</b> {customer} | <b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
            story.append(Spacer(1, 10))
            
            table_data = [["Item Name", "HSN", "Qty", "Price", "Tax %", "Total"]]
            for item in items:
                table_data.append([
                    item["item_name"], item.get("hsn_code", ""), str(item["qty"]), 
                    f"₹{item['price']:.2f}", f"{item['tax_rate']}%", f"₹{item['total_amount']:.2f}"
                ])
            
            t = Table(table_data, colWidths=[150, 70, 50, 80, 60, 100])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('PADDING', (0,0), (-1,-1), 6)
            ]))
            story.append(t)
            story.append(Spacer(1, 15))
            story.append(Paragraph(f"<b>Total Tax:</b> ₹{t_tax:,.2f}", styles['Normal']))
            story.append(Paragraph(f"<b>Grand Total:</b> ₹{g_total:,.2f}", styles['Heading3']))
            
            doc.build(story)
            buffer.seek(0)
            return buffer

        if st.button("Commit & Generate Invoice PDF", type="primary"):
            try:
                cur_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                bill_payload = {
                    "date": cur_date,
                    "customer_name": cust_name,
                    "grand_total": grand_total,
                    "payment_method": "Bank / Cash",
                    "invoice_type": inv_type,
                    "txn_category": "Sales",
                    "total_tax": total_tax
                }
                res = supabase.table("bills").insert(bill_payload).execute()
                if res.data:
                    b_no = res.data[0]["bill_no"]
                    for item in st.session_state.sales_cart:
                        supabase.table("bill_items").insert({
                            "bill_no": b_no,
                            "item_name": item["item_name"],
                            "qty": item["qty"],
                            "price": item["price"],
                            "tax_rate": item["tax_rate"],
                            "tax_amount": item["tax_amount"],
                            "total_amount": item["total_amount"]
                        }).execute()
                    
                    st.success(f"Invoice #{b_no} successfully committed!")
                    
                    pdf_buf = generate_pdf_invoice(b_no, cust_name, st.session_state.sales_cart, grand_total, total_tax)
                    st.download_button(
                        label="📥 Download Invoice PDF",
                        data=pdf_buf,
                        file_name=f"Invoice_{b_no}.pdf",
                        mime="application/pdf"
                    )
                    st.session_state.sales_cart = []
            except Exception as e:
                st.error(f"Failed to commit invoice: {e}")
    else:
        st.info("Your sales cart is empty. Add items from inventory first.")

# --- MODULE 3: INVENTORY CONTROL ---
elif nav_choice == "📦 Inventory Control":
    st.subheader("📦 Inventory Stock Management")
    
    col1, col2 = st.columns(2)
    with col1:
        i_name = st.text_input("Item Name")
        i_stock = st.number_input("Stock Quantity", min_value=0, value=10)
    with col2:
        i_price = st.number_input("Unit Price (₹)", min_value=0.0, value=100.0)
        i_hsn = st.text_input("HSN Code", value="")

    if st.button("Save Item to Inventory"):
        if not i_name:
            st.error("Item name is required.")
        else:
            try:
                supabase.table("inventory").upsert({
                    "item_name": i_name, "stock": i_stock, "price": i_price, "hsn_code": i_hsn
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

# --- MODULE 4: PARTIES & CUSTOMERS LEDGER ---
elif nav_choice == "👥 Parties & Customers Ledger":
    st.subheader("👥 Party & Customer Management")
    
    p_name = st.text_input("Party / Buyer Company Name")
    p_phone = st.text_input("Phone Number")
    p_gstin = st.text_input("GSTIN")
    p_addr = st.text_area("Address")
    
    if st.button("Save Party Profile"):
        if not p_name:
            st.error("Party Name is required.")
        else:
            try:
                supabase.table("parties").upsert({
                    "party_name": p_name, "phone": p_phone, "gstin": p_gstin, "address": p_addr
                }, on_conflict="party_name").execute()
                st.success("Party registered successfully!")
            except Exception as e:
                st.error(f"Error saving party: {e}")
                
    try:
        parties_data = supabase.table("parties").select("*").execute()
        if parties_data.data:
            st.markdown("### Registered Parties")
            st.dataframe(pd.DataFrame(parties_data.data))
    except Exception:
        pass

# --- MODULE 5: INVOICES & AUDIT LOGS ---
elif nav_choice == "📊 Invoices & Audit Logs":
    st.subheader("📊 Master Invoices & Audit Logs")
    try:
        bills_data = supabase.table("bills").select("*").execute()
        if bills_data.data:
            st.markdown("### Generated Invoices Console")
            st.dataframe(pd.DataFrame(bills_data.data))
        else:
            st.info("No invoices found.")
    except Exception as e:
        st.error(f"Failed to load invoices: {e}")
