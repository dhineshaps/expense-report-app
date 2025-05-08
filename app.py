import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from datetime import date
import gspread
from google.oauth2.service_account import Credentials


footer="""<style>
#MainMenu {visibility: hidden; }
.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
background-color: white;
color: black;
text-align: center;
}
</style>
<div class="footer">
<p>Developed with ❤️ By The FET Quest<a style='display: block; text-align: center</p>
</div>
"""

# --- Load Auth Config ---
config = yaml.safe_load(st.secrets["auth"]["config"])

# --- Setup Authenticator ---
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- Title and Login ---
st.title("📒 Expense Tracker")

name, authentication_status, username = authenticator.login('Login','main')

# --- Authenticated Logic ---
if authentication_status:
    st.success(f"👋 Welcome, {name}!")
    authenticator.logout('Logout', 'main')

    # --- Page Navigation ---
    page = st.radio("Go to", ["Home", "Add Expense", "Reports"], horizontal=True)

    @st.cache_resource
    def get_gspread_client():
        creds_dict = st.secrets["connections"]["expense"]
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(creds)

    def insert_data(client, spreadsheet_id, sheet_name, data):
        sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
        next_row = len(sheet.get_all_values()) + 1
        sheet.update_cell(next_row, 3, data[0])
        sheet.update_cell(next_row, 4, data[1])
        sheet.update_cell(next_row, 5, data[2])
        sheet.update_cell(next_row, 6, data[3])
        return next_row

    # --- Page Logic ---
    if page == "Home":
        st.write("🏠 Welcome to the Expense Tracker home page.")

    elif page == "Add Expense":
        with st.form("expense_form"):
            st.subheader("Enter Expense Details")
            date_input = st.date_input("📅 Date", value=date.today())
            formatted_date = date_input.strftime("%d-%m-%Y")
            category = st.selectbox("📂 Category", (
                "Grocery", "Vegetables", "Fruits", "Gas", "Snacks", "Entertainment",
                "Tickets", "Rent", "Home Maint", "Tea and Snacks", "Food", "Non-Veg",
                "Egg", "Personal wellness", "Others"
            ))
            expense = st.text_input("💸 Expense")
            items = st.text_input("🛒 Items")
            submit = st.form_submit_button("Submit")

        if submit:
            if not expense.replace('.', '', 1).isdigit():
                st.error("💡 Expense should be a numeric value.")
            elif not (formatted_date and category and expense and items):
                st.error("❌ Please fill in all fields.")
            else:
                client = get_gspread_client()
                spreadsheet_id = "1WZdCZkGldtU2SgACrThKUFhaemRWwqYwuCVKwF1402g"
                sheet_name = "May_2025"
                row = insert_data(client, spreadsheet_id, sheet_name, [formatted_date, category, expense, items])
                st.success(f"✅ Data inserted successfully into row {row}.")

    elif page == "Reports":
        st.write("📊 Reports page is under construction.")

elif authentication_status is False:
    st.error("❌ Username/password is incorrect")

elif authentication_status is None:
    st.info("🔐 Please enter your username and password")
