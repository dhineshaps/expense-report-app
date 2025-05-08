import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from datetime import date
from oauth2client.service_account import ServiceAccountCredentials
import gspread

# Load config from secrets
config = yaml.safe_load(st.secrets["auth"]["config"])

# Setup authentication
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config.get('preauthorized', {})
)

# --- Page selection ---
page = st.radio("Go to", ["Home", "Add Expense", "Reports"], horizontal=True)

# --- Login ---
st.title("📒 Expense Tracker")
name, authentication_status, username = authenticator.login("Login", location="main")  # <- FIXED login line

# --- Main Logic ---
if authentication_status:
    st.success(f"👋 Welcome, {name}!")
    authenticator.logout("Logout", location="main")

    @st.cache_resource
    def get_gspread_client():
        creds_dict = st.secrets["connections"]["expense"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client

    def insert_data(client, spreadsheet_id, sheet_name, data):
        sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
        next_row = len(sheet.get_all_values()) + 1
        sheet.update_cell(next_row, 3, data[0])
        sheet.update_cell(next_row, 4, data[1])
        sheet.update_cell(next_row, 5, data[2])
        sheet.update_cell(next_row, 6, data[3])
        return next_row

    # --- Form Logic ---
    if page == "Add Expense":
        with st.form("expense_form"):
            st.subheader("Enter Expense Details")
            Date = st.date_input("📅 Date", value=date.today())
            col1 = Date.strftime("%d-%m-%Y")
            col2 = st.selectbox("📂 Category", (
                "Grocery", "Vegetables", "Fruits", "Gas", "Snacks", "Entertainment",
                "Tickets", "Rent", "Home Maint", "Tea and Snacks", "Food", "Non-Veg",
                "Egg", "Personal wellness", "Others"
            ))
            col3 = st.text_input("💸 Expense")
            col4 = st.text_input("🛒 Items")
            submit = st.form_submit_button("Submit")

        if submit:
            if not col3.replace('.', '', 1).isdigit():
                st.error("Expense should be a numeric value. Please re-enter the correct value.")
            elif not (col1 and col2 and col3 and col4):
                st.error("❌ Please fill in all fields.")
            else:
                client = get_gspread_client()
                spreadsheet_id = "1WZdCZkGldtU2SgACrThKUFhaemRWwqYwuCVKwF1402g"
                sheet_name = "May_2025"
                next_row = insert_data(client, spreadsheet_id, sheet_name, [col1, col2, col3, col4])
                st.success(f"✅ Data inserted successfully into row {next_row}.")

    elif page == "Home":
        st.write("🏠 Welcome to the Expense Tracker home page.")
    elif page == "Reports":
        st.write("📊 Reports page is under construction.")

elif authentication_status is False:
    st.error("❌ Username/password is incorrect")
elif authentication_status is None:
    st.info("🔐 Please enter your username and password")
