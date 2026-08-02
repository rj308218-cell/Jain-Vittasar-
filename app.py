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
if "is_master" not in st.session_state:
    st.session_state.is_master = False
# ==========================================
# AUTHENTICATION & SIGNUP GATEWAY
# ==========================================
def auth_gateway():
    st.title("🏢 JAIN VITTASAR - CLOUD GATEWAY")
    st.markdown("### Financial Intelligence & Billing Platform")
    
    tab1, tab2, tab3 = st.tabs(["Customer Login", "Master Login", "New Registration & Signup"])
    
    # Fetch Master Configurations safely from Supabase
    try:
        cfg_res = supabase.table("master_config").select("*").execute()
        config_data = {row["key"]: row["value"] for row in cfg_res.data} if cfg_res.data else {}
    except Exception:
        config_data = {}

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
                        
                        # Check subscription expiry deadline
                        # Check subscription expiry deadline
                        created_at = datetime.strptime(account["created_at"], "%Y-%m-%d %H:%M:%S")
                        plan_days = int(account.get("plan_days", 30))
                        expiry_date = created_at + pd.Timedelta(days=plan_days)
                        
                        st.session_state.authenticated = True
                        st.session_state.is_master = False
                        
                        # Set subscription status flag instead of completely blocking access[cite: 3]
                        if datetime.now() > expiry_date:
                            st.session_state.subscription_expired = True
                            st.warning(f"Your subscription expired on {expiry_date.strftime('%Y-%m-%d')}. Access is restricted to Data Backup and Plan Renewal.")[cite: 3]
                        else:
                            st.session_state.subscription_expired = False
                            
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
        st.subheader("Master / Creator Login")
        m_id = st.text_input("Master ID", value="Admin", key="m_id_box")
        m_pwd = st.text_input("Master Password", type="password", value="Rj308218@gmail", key="m_pwd_box")
        
        if st.button("Authorize Master Access", key="m_auth_btn"):
            if m_id == "Admin" and m_pwd == "Rj308218@gmail":
                st.session_state.authenticated = True
                st.session_state.is_master = True
                st.session_state.company = {"name": "Software Creator Portal", "gstin": "MASTER-ROOT"}
                st.success("Master Creator Access Granted.")
                st.rerun()
            else:
                st.error("Invalid Master Creator Credentials!")

    with tab3:
        st.subheader("New Business Registration & Subscription")
        reg_biz = st.text_input("Business Name *", key="reg_biz")
        reg_owner = st.text_input("Owner Full Name *", key="reg_owner")
        reg_email = st.text_input("Email Address *", key="reg_email")
        reg_mobile = st.text_input("Mobile Number *", key="reg_mobile")
        reg_addr = st.text_area("Office Address *", key="reg_addr")
        
        has_gstin = st.checkbox("Do you have a GSTIN?", key="reg_has_gstin")
        reg_gstin = st.text_input("GSTIN Number", key="reg_gstin") if has_gstin else ""
        
        st.markdown("---")
        st.markdown("### Select Subscription & Payment")
        
        # Load Plans dynamically from Master Settings
        import json
        default_plans = [
            {"name": "1 Day Plan", "price": 10, "days": 1},
            {"name": "1 Month Plan", "price": 250, "days": 30},
            {"name": "Custom Plan (90 Days)", "price": 600, "days": 90}
        ]
        plans = json.loads(config_data.get("subscription_plans", json.dumps(default_plans)))
        plan_options = {f"{p['name']} (₹{p['price']})": p for p in plans}
        
        sel_plan_label = st.selectbox("Select Subscription Plan", list(plan_options.keys()))
        chosen_plan = plan_options[sel_plan_label]
        
        st.info(f"Amount to Pay: **₹{chosen_plan['price']}** for **{chosen_plan['days']} Days** validity.")
        
        # Display Creator's Payment Instructions / QR / UPI
        st.markdown("#### 💳 Payment Instructions")
        col_pay1, col_pay2 = st.columns(2)
        with col_pay1:
            st.write(f"**UPI ID:** {config_data.get('upi_id', 'Not Set')}")
            st.write(f"**Bank Name:** {config_data.get('bank_name', 'Not Set')}")
            st.write(f"**Account No:** {config_data.get('account_no', 'Not Set')}")
            st.write(f"**IFSC Code:** {config_data.get('ifsc', 'Not Set')}")
        with col_pay2:
            qr_link = config_data.get('qr_code_url', '')
            if qr_link:
                st.image(qr_link, width=160, caption="Scan & Pay via UPI")
            else:
                st.warning("QR Code not uploaded by Master yet.")

        txn_ref = st.text_input("Enter UPI Transaction ID / UTR Number after payment *", key="reg_txn_ref")
        
        reg_user = st.text_input("Create Username *", key="reg_user")
        reg_pwd = st.text_input("Create Password *", type="password", key="reg_pwd")

        if st.button("Complete Registration", type="primary"):
            if not reg_biz or not reg_owner or not reg_email or not reg_mobile or not reg_addr or not reg_user or not reg_pwd or not txn_ref:
                st.error("Please fill out all required fields and enter your payment Transaction ID (UTR).")
            else:
                try:
                    # Check for existing username or email or gstin to prevent duplicates[cite: 3]
                    check_user = supabase.table("users").select("id").eq("username", reg_user).execute()
                    check_email = supabase.table("users").select("id").eq("mobile", reg_mobile).execute() # checking unique channel
                    
                    # Check company profile for existing gstin or name if applicable
                    check_gstin = supabase.table("company_profile").select("name").eq("gstin", reg_gstin).execute() if reg_gstin else type('obj', (object,), {'data': []})

                    if check_user.data:
                        st.error("Username already taken! Choose another.")
                    elif check_email.data or (reg_gstin and check_gstin.data):
                        st.error("This e-mail is already registered please try to sign in.")[cite: 3]
                    else:
                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        user_payload = {
                            "company_name": reg_biz,
                            "owner_name": reg_owner,
                            "mobile": reg_mobile,
                            "address": reg_addr,
                            "gstin": reg_gstin,
                            "plan_name": chosen_plan["name"],
                            "plan_days": chosen_plan["days"],
                            "amount_paid": chosen_plan["price"],
                            "txn_ref": txn_ref,
                            "username": reg_user,
                            "password": reg_pwd,
                            "created_at": now_str
                        }
                        supabase.table("users").insert(user_payload).execute()

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
# ==========================================
# DASHBOARD NAVIGATION CONSOLE
# ==========================================
st.sidebar.title("Navigation Console")
if st.session_state.get("is_master", False):
    nav_choice = st.sidebar.radio("Master Portal", [
        "👑 Master Control Panel",
        "👥 Manage All Users & Subscriptions",
        "💳 Payment Gateway Setup",
        "⚙️ Plan Pricing & Customizer"
    ])
else:
    # Restructured into the 5 exact tabs with sub-options as requested in Doc1[cite: 3]
    main_tab = st.sidebar.radio("Go to", [
        "🏠 Home Tab", 
        "📄 Invoices", 
        "📊 Reports",
        "💰 Cash & Accounts",
        "📦 Inventory & Parties"
    ])
    
    # Sub-menu choices mapping based on selection
    if main_tab == "🏠 Home Tab":
        sub_choice = st.sidebar.selectbox("Home Options", ["Create New Company", "Update Company Data", "Back Up Your Data", "Subscription Plans"])
        nav_choice = f"Home: {sub_choice}"
    elif main_tab == "📄 Invoices":
        sub_choice = st.sidebar.selectbox("Invoice Options", ["Sales Invoice", "Credit Note", "Purchase Receipt", "Debit Note", "Daily Ledger"])
        nav_choice = f"Invoice: {sub_choice}"
    elif main_tab == "📊 Reports":
        sub_choice = st.sidebar.selectbox("Report Options", ["View Party Ledger", "View Inventory Ledger", "View All Bills Ledger"])
        nav_choice = f"Report: {sub_choice}"
    elif main_tab == "💰 Cash & Accounts":
        sub_choice = st.sidebar.selectbox("Accounts Options", ["Cash", "Bank Account", "Add New Bank Account"])
        nav_choice = f"Account: {sub_choice}"
    else:
        sub_choice = st.sidebar.selectbox("Manage", ["Inventory Control", "Parties & Customers Ledger"])
        nav_choice = f"Manage: {sub_choice}"

st.sidebar.markdown("---")
if st.sidebar.button("🔒 Logout Session"):
    st.session_state.authenticated = False
    st.session_state.company = None
    st.session_state.is_master = False
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

    # Added Business Logo Upload Option (JPEG/JPG/PNG)[cite: 3]
    st.markdown("### Business Logo")
    logo_file = st.file_uploader("Upload Company Logo (JPEG/JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    logo_url = c_active.get("logo_url", "")
    if logo_file is not None:
        # For local file storage or handling bytes in session
        logo_url = logo_file.name

    if st.button("Save Profile to Cloud", type="primary"):
        if not c_name or not c_gstin:
            st.error("Company Name and GSTIN are required.")
        else:
            payload = {
                "name": c_name, "address": c_addr, "phone": c_phone, 
                "gstin": c_gstin, "pan": c_pan, "bank_name": c_bank, 
                "account_no": c_acc, "ifsc": c_ifsc, "logo_url": logo_url
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
            
            # Header matching official billing format style[cite: 2]
            story.append(Paragraph(f"<b>TAX INVOICE</b>", styles['Heading2']))
            story.append(Paragraph(f"<b>{comp.get('name', 'Jain Vittasar Enterprise')}</b>", styles['Heading1']))
            story.append(Paragraph(f"Address: {comp.get('address', 'N/A')} | GSTIN/UIN: {comp.get('gstin', 'N/A')}", styles['Normal']))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph(f"<b>Invoice No:</b> BE/26-27/{bill_no} | <b>Dated:</b> {datetime.now().strftime('%d-%b-%y')}", styles['Normal']))
            story.append(Paragraph(f"<b>Buyer (Bill to):</b> {customer}", styles['Normal']))
            story.append(Spacer(1, 10))
            
            # Detailed item columns matching Sales format[cite: 2]
            table_data = [["SI No", "Description of Goods", "HSN/SAC", "Quantity", "Rate", "Amount"]]
            for idx, item in enumerate(items, 1):
                base_amt = item["qty"] * item["price"]
                table_data.append([
                    str(idx), 
                    item["item_name"], 
                    item.get("hsn_code", "85446090"), 
                    f"{item['qty']} MTR", 
                    f"₹{item['price']:.2f}", 
                    f"₹{base_amt:.2f}"
                ])
            
            t = Table(table_data, colWidths=[40, 180, 70, 70, 75, 75])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('PADDING', (0,0), (-1,-1), 5),
                ('FONTSIZE', (0,0), (-1,-1), 9)
            ]))
            story.append(t)
            story.append(Spacer(1, 10))
            
            # Tax breakdown split (CGST & SGST)[cite: 2]
            half_tax = t_tax / 2.0
            story.append(Paragraph(f"<b>OUTPUT CGST:</b> ₹{half_tax:,.2f}", styles['Normal']))
            story.append(Paragraph(f"<b>OUTPUT SGST:</b> ₹{half_tax:,.2f}", styles['Normal']))
            story.append(Spacer(1, 5))
            story.append(Paragraph(f"<b>Grand Total:</b> ₹{g_total:,.2f}", styles['Heading3']))
            
            # Amount in words & Declarations[cite: 2]
            try:
                words_str = num2words(int(g_total), lang='en_IN').title()
            except Exception:
                words_str = str(g_total)
            
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"<b>Amount Chargeable (in words):</b> INR {words_str} Only", styles['Normal']))
            story.append(Spacer(1, 15))
            story.append(Paragraph("<b>Declaration:</b> We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct.", styles['Normal']))
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>SUBJECT TO MEERUT JURISDICTION | E. & O.E</b>", styles['Normal']))
            story.append(Paragraph("This is a Computer Generated Invoice", styles['Normal']))
            
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
# --- MASTER MODULE 1: MASTER CONTROL PANEL & ANALYTICS ---
if st.session_state.get("is_master", False) and nav_choice == "👑 Master Control Panel":
    st.subheader("👑 Software Creator & Master Dashboard")
    try:
        users_res = supabase.table("users").select("*").execute()
        total_users = len(users_res.data) if users_res.data else 0
        total_revenue = sum(float(u.get("amount_paid", 0)) for u in users_res.data) if users_res.data else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Registered Businesses", total_users)
        col2.metric("Total Platform Revenue (₹)", f"₹ {total_revenue:,.2f}")
        col3.metric("System Status", "Live & Healthy")
        
        st.markdown("### Recent Signups")
        if users_res.data:
            st.dataframe(pd.DataFrame(users_res.data)[['company_name', 'owner_name', 'mobile', 'plan_name', 'amount_paid', 'created_at']])
    except Exception as e:
        st.error(f"Error loading master data: {e}")

# --- MASTER MODULE 2: MANAGE USERS & SUBSCRIPTIONS ---
elif st.session_state.get("is_master", False) and nav_choice == "👥 Manage All Users & Subscriptions":
    st.subheader("👥 User Account & Subscription Manager")
    try:
        users_res = supabase.table("users").select("*").execute()
        if users_res.data:
            for u in users_res.data:
                with st.expander(f"Business: {u['company_name']} ({u['username']})"):
                    st.write(f"**Owner:** {u['owner_name']} | **Mobile:** {u['mobile']}")
                    st.write(f"**Current Plan:** {u['plan_name']} | **Paid:** ₹{u.get('amount_paid', 0)} | **Registered:** {u['created_at']}")
                    
                    new_validity = st.number_input("Extend Plan Validity (Days)", min_value=1, value=30, key=f"ext_{u['id']}")
                    if st.button("Update Expiry / Extend Plan", key=f"btn_ext_{u['id']}"):
                        supabase.table("users").update({"plan_days": u.get("plan_days", 30) + new_validity}).eq("id", u["id"]).execute()
                        st.success("Subscription extended successfully!")
                        st.rerun()
                        
                    if st.button("🗑️ Delete / Block User", key=f"del_{u['id']}"):
                        supabase.table("users").delete().eq("id", u["id"]).execute()
                        st.warning("User account removed.")
                        st.rerun()
    except Exception as e:
        st.error(f"Failed to fetch users: {e}")

# --- MASTER MODULE 3: PAYMENT GATEWAY SETUP ---
elif st.session_state.get("is_master", False) and nav_choice == "💳 Payment Gateway Setup":
    st.subheader("💳 Configure Creator Payment Gateways")
    
    try:
        cfg_res = supabase.table("master_config").select("*").execute()
        cfg_map = {row["key"]: row["value"] for row in cfg_res.data} if cfg_res.data else {}
    except Exception:
        cfg_map = {}
        
    upi_input = st.text_input("Master UPI ID", value=cfg_map.get("upi_id", ""))
    bank_input = st.text_input("Bank Name", value=cfg_map.get("bank_name", ""))
    acc_input = st.text_input("Account Number", value=cfg_map.get("account_no", ""))
    ifsc_input = st.text_input("IFSC Code", value=cfg_map.get("ifsc", ""))
    qr_url_input = st.text_input("QR Code Image Direct URL", value=cfg_map.get("qr_code_url", ""))

    if st.button("Save Payment Configurations", type="primary"):
        configs = [
            {"key": "upi_id", "value": upi_input},
            {"key": "bank_name", "value": bank_input},
            {"key": "account_no", "value": acc_input},
            {"key": "ifsc", "value": ifsc_input},
            {"key": "qr_code_url", "value": qr_url_input}
        ]
        for c in configs:
            supabase.table("master_config").upsert(c, on_conflict="key").execute()
        st.success("Payment details updated live for all new customer signups!")

# --- MASTER MODULE 4: PLAN PRICING & CUSTOMIZER ---
elif st.session_state.get("is_master", False) and nav_choice == "⚙️ Plan Pricing & Customizer":
    st.subheader("⚙️ Subscription Plans Creator & Editor")
    
    import json
    try:
        cfg_res = supabase.table("master_config").select("value").eq("key", "subscription_plans").execute()
        current_plans = json.loads(cfg_res.data[0]["value"]) if cfg_res.data else [
            {"name": "1 Day Plan", "price": 10, "days": 1},
            {"name": "1 Month Plan", "price": 250, "days": 30},
            {"name": "Custom Plan (90 Days)", "price": 600, "days": 90}
        ]
    except Exception:
        current_plans = []

    st.write("### Active Subscription Plans")
    updated_plans = []
    for idx, p in enumerate(current_plans):
        col_p1, col_p2, col_p3, col_p4 = st.columns([3, 2, 2, 1])
        with col_p1:
            p_name = st.text_input("Plan Name", value=p["name"], key=f"p_name_{idx}")
        with col_p2:
            p_price = st.number_input("Price (₹)", value=int(p["price"]), key=f"p_price_{idx}")
        with col_p3:
            p_days = st.number_input("Validity (Days)", value=int(p["days"]), key=f"p_days_{idx}")
        with col_p4:
            keep_plan = st.checkbox("Keep", value=True, key=f"p_keep_{idx}")
        
        if keep_plan:
            updated_plans.append({"name": p_name, "price": p_price, "days": p_days})

    st.markdown("---")
    st.write("#### Add New Plan")
    new_p_name = st.text_input("New Plan Name")
    new_p_price = st.number_input("New Plan Price (₹)", min_value=0, value=500)
    new_p_days = st.number_input("New Plan Validity (Days)", min_value=1, value=365)

    if st.button("Add Plan"):
        if new_p_name:
            updated_plans.append({"name": new_p_name, "price": new_p_price, "days": new_p_days})
            st.success("Plan added! Click 'Save All Plan Changes' below.")

    if st.button("Save All Plan Changes", type="primary"):
        payload = {"key": "subscription_plans", "value": json.dumps(updated_plans)}
        supabase.table("master_config").upsert(payload, on_conflict="key").execute()
        st.success("Subscription plans updated successfully across the app!")
        st.rerun()
