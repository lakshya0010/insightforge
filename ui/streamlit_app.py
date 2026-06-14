import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(__file__))
import api_client as api

st.set_page_config(
    page_title="InsightForge",
    page_icon="💰",
    layout="centered"
)

st.markdown("""
<style>
    .main { max-width: 800px; }
    .stButton > button {
        width: 100%;
        background-color: #6366f1;
        color: white;
        border: none;
        padding: 0.5rem;
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #4f46e5;
    }
    .metric-card {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin: 0.5rem 0;
    }
</style>""", unsafe_allow_html=True)


def is_logged_in() -> bool:
    return "token" in st.session_state and st.session_state["token"]

def logout():
    st.session_state.clear()
    st.rerun()


def show_auth_page():
    st.title("InsightForge")
    st.subheader("Your AI-Powered Finance Analyzer")
    st.write("Upload your bank statement and get instant spending insights.")

    st.divider()

    tab1,tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Welcome Back!")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password",key = "login_password")

        if st.button("Login", key="login_btn"):
            if not email or not password:
                st.error("Please fill in all the fields")
            else:
                with st.spinner("Logging in..."):
                    result = api.login(email, password)

                if result.get("success"):
                    st.session_state["token"] = result["data"]["access_token"]
                    st.success("Loggen in successfully")
                    st.rerun()
                else:
                    error = result.get("error", {})
                    st.error(error.get("message", "login failed"))

    
    with tab2:
        st.subheader("Create an account")
        name = st.text_input("full name", key="reg_name")
        email = st.text_input("email", key="reg_email")
        password = st.text_input("password", type="password", key = "reg_password")

        if st.button("Register", key = "reg_btn"):
            if not name or not email or not password:
                st.error("Please fill in all fields")
            else:
                with st.spinner("Creating account..."):
                    result = api.register(name,email,password)
                if result.get("success"):
                    st.success("Account created! Please login.")
                else:
                    error = result.get("error", {})
                    st.error(error.get("message", "Registration failed"))
                


def show_dashboard():
    with st.sidebar:
        st.title("InsightForge")
        st.divider()
        if st.button("Logout"):
            logout()
        
    st.title("Your Statements")

    st.subheader("Upload New Statement")
    uploaded_file = st.file_uploader(
        "Choose a PDF(or CSV) file",
        type=["csv","pdf"],
        help="PDF recommended. CSV supported for select bank formats."
    )
    st.caption("Note: Currently optimized for monthly statements.")

    if uploaded_file and st.button("Analyze Statement"):
        with st.spinner("Analyzing your statement... This may take 10-15 seconds."):
            result = api.upload_statement(
                token=st.session_state["token"],
                file_bytes=uploaded_file.read(),
                filename=uploaded_file.name
            )

        if result.get("success"):
            st.success("Statement analyzed successfully")
            st.session_state["view_statement_id"] = result["data"]["id"]
            st.rerun()
        else:
            error = result.get("error", {})
            message = error.get("message", "Unknown error")
            st.error(f"Upload failed: {message}")
    
            with st.expander("Error details"):
                st.json(result)

    st.divider()

    st.subheader("Past Statements")

    with st.spinner("Loading..."):
        result = api.get_statements(st.session_state["token"])

    if result.get("success"):
        statements = result["data"]
        if not statements:
            st.info("No statements yet. Upload your first one above!")
        else:
            for s in statements:
                col1, col2, col3 = st.columns([3,2,1])
                with col1:
                    st.write(f"📄 **{s['filename']}**")
                with col2:
                    st.write(f"📅 {s['month']}")
                with col3:
                    if st.button("View", key=f"view_{s['id']}"):
                        st.session_state["view_statement_id"] = s["id"]
                        st.rerun()

    else:
        st.error("Failed to load statements")


def show_statement_detail(statement_id:int):
    with st.sidebar:
        st.title("InsightForge")
        st.divider()
        if st.button("<- Back to Dashboard"):
            del st.session_state["view_statement_id"]
            st.rerun()
        if st.button("Logout"):
            logout()
    
    with st.spinner("Loading statement..."):
        result = api.get_statement_detail(
            st.session_state["token"],
            statement_id
        )
    if not result.get("success"):
        st.error("Failed to load statement")
        return
    
    data  = result["data"]
    report = data.get("report")
    transactions = data.get("transactions", [])

    st.title(f"📄 {data['filename']}")
    st.caption(f"Month: {data['month']} · Status: {data['status']}")

    if report:
        st.divider()
        st.subheader("AI Spending Report")
        st.write(report["summary"])

        st.divider()
        st.subheader("📊 Financial Summary")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Income", f"₹{float(report['total_income']):,.0f}")
        with col2:
            st.metric("Total Expenses", f"₹{float(report['total_expenses']):,.0f}")
        with col3:
            savings = float(report['total_income']) - float(report['total_expenses'])
            st.metric("Net Savings", f"₹{savings:,.0f}")

        if report.get("category_breakdown"):
            st.divider()
            st.subheader("🏷️ Spending by Category")
            breakdown = report["category_breakdown"]
            df_breakdown = pd.DataFrame(
                list(breakdown.items()),
                columns=["Category", "Amount (₹)"]
            ).sort_values("Amount (₹)", ascending=False)
            st.dataframe(df_breakdown, use_container_width=True, hide_index=True)
        
        # Top transfers
        if report.get("top_transfers"):
            st.divider()
            st.subheader("👥 Top People You Transacted With")
            transfers = report["top_transfers"]
            df_transfers = pd.DataFrame(
                list(transfers.items()),
                columns=["Person", "Total Amount (₹)"]
            ).sort_values("Total Amount (₹)", ascending=False)
            st.dataframe(df_transfers, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📋 All Transactions")

    if transactions:
        df = pd.DataFrame([{
            "Date": t["date"],
            "Description": t["description"],
            "Amount (₹)": float(t["amount"]),
            "Type": t["type"].capitalize(),
            "Category": t["category"] or "Uncategorized"
        } for t in transactions])

        st.dataframe(df, use_container_width=True, hide_index=True)

    else:
        st.info("No transactions found")


def main():
    if not is_logged_in():
        show_auth_page()
    elif "view_statement_id" in st.session_state:
        show_statement_detail(st.session_state["view_statement_id"])
    else:
        show_dashboard()

if __name__ == "__main__":
    main()

