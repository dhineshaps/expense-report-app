import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from datetime import date

st.set_page_config(page_title="Expense Tracker", page_icon = im,layout="wide")

# --- Reset logic ---
if "reset_triggered" in st.session_state and st.session_state.reset_triggered:
    st.session_state.expense_input = ""
    st.session_state.items_input = ""
    st.session_state.category_input = "Grocery"
    st.session_state.date_input = date.today()
    st.session_state.reset_triggered = False
    st.rerun()

# --- Title ---
left_co, cent_co, last_co = st.columns(3)
with cent_co:
    new_title = '<p style="font-family:fantasy; color:#DAA520; font-size: 42px;">The FET Quest</p>'
    st.markdown(new_title, unsafe_allow_html=True)

footer = """
<style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: white;
        color: black;
        text-align: center;
        padding: 10px;
        font-size: 16px;
        z-index: 9999;
        border-top: 1px solid #ccc;
    }

    /* Give some padding to Streamlit’s main block so content doesn’t get hidden */
    .stApp {
        padding-bottom: 60px;  /* Adjust based on footer height */
    }
</style>
<div class="footer">
    Developed with ❤️ by <strong>The FET Quest</strong>
</div>
"""

st.markdown(footer, unsafe_allow_html=True)


# --- Auth Config ---
config = yaml.safe_load(st.secrets["auth"]["config"])
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

st.title("📒 Expense Tracker")
name, authentication_status, username = authenticator.login('Login', 'main')

date_input = date.today()
date1 = date_input.strftime("%d-%m-%Y")
Mon = int(date1.split("-")[1])
yr = int(date1.split("-")[2])

if (Mon == 1):
    Month = "Jan"
elif (Mon == 2):
    Month = "Feb"
elif (Mon == 3):
    Month = "Mar"
elif (Mon == 4):
    Month = "Apr" 
elif (Mon == 5):
    Month = "May"
elif (Mon == 6):
    Month = "Jun"
elif (Mon == 7):
    Month = "July"   
elif (Mon == 8):
    Month = "Aug"
elif (Mon == 9):
    Month = "Sep"
elif (Mon == 10):
    Month = "Oct"
elif (Mon == 11):
    Month = "Nov"
elif (Mon == 12):
    Month = "Dec"

Sheet = str(Month)+'_'+str(yr)+'_'+"Test"

# --- Google Sheets Client ---
@st.cache_resource
def get_gspread_client():
    creds_dict = st.secrets["connections"]["expense"]
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(creds)

# --- Find next empty row based on column group ---
def get_next_available_row(sheet, column_letters, start_row=2):
    max_row = start_row
    for col_letter in column_letters:
        col_index = ord(col_letter.upper()) - 64
        values = sheet.col_values(col_index)
        last_filled = next((i for i, v in reversed(list(enumerate(values, start=1))) if v.strip()), 0)
        if last_filled + 1 > max_row:
            max_row = last_filled + 1
    return max_row

# --- Insert data into mapped columns ---
def insert_mapped_data(sheet, data_map):
    for col, (r, val) in data_map.items():
        sheet.update_acell(f"{col}{r}", val)
    return r

# --- Main Logic ---
if authentication_status:
    st.success(f"👋 Welcome, {name}!")
    authenticator.logout('Logout', 'main')

    page = st.radio("Go to", ["Add Home Expense", "Add Personal Expense", "Purchase from Reserve",
    "Savings","Investment", "Reports"], horizontal=True)

    if page in ["Add Home Expense", "Add Personal Expense", "Purchase from Reserve","Savings","Investment"]:
        if page == "Add Personal Expense":
            st.write("Dhinesh's Personal Expenses Only")
        with st.form("expense_form"):
            st.subheader("Enter Expense Details")
            date_input = st.date_input("📅 Date", value=st.session_state.get("date_input", date.today()), key="date_input")
            formatted_date = date_input.strftime("%d-%m-%Y")
            if page == "Add Home Expense":
                category = st.selectbox("📂 Category", (
                    "Grocery", "Vegetables", "Fruits", "Gas", "Snacks", "Entertainment",
                    "Tickets", "Rent", "Home Maint", "Tea and Snacks", "Food", "Non-Veg",
                    "Egg", "Personal wellness", "Others"
                ), key="category_input")
            elif page == "Add Personal Expense":
                category = st.selectbox("📂 Category", (
                "EMI", "Dad", "Vijaya" ,"Tea and Snacks","Fruits","Snacks", "Entertainment","Juice",
                "Donation","Tickets", "Lent","Loan Repayment," "Home Maint","Food",
                "Non-Veg","Egg", "Personal wellness","Ecommerce","Others"
                 ), key="category_input")
            elif page == "Purchase from Reserve":
                category = st.selectbox("📂 Category", (
                "Donation", "Lent","Loan Repayment," "Home Maint","Personal wellness","Ecommerce","Others",
                "Gift"
                 ), key="category_input")
            elif page == "Savings":
                category = st.selectbox("📂 Category", (
                "Last Month Pass Over", "Gift","Others"
                 ), key="category_input")
            elif page == "Investment":
                category = st.selectbox("📂 Category", (
                "Gold", "Equity","Bonds","Mutual Funds"
                 ), key="category_input")
            if page == "Savings":
                expense = st.text_input("💸 Savings in Rs.", key="expense_input")
            else:
                expense = st.text_input("💸 Expense in Rs.", key="expense_input")
            items = st.text_input("🛒 Items", key="items_input")
            submit = st.form_submit_button("Submit")
            reset = st.form_submit_button("Reset")

        if submit:
            if not expense.replace('.', '', 1).isdigit():
                st.error("💡 Expense should be a numeric value.")
            elif not (formatted_date and category and expense and items):
                st.error("❌ Please fill in all fields.")
            else:
                client = get_gspread_client()
                spreadsheet_id = "1r2OjJNEFZKKHtQ7CMwman06YGFewptPheL2D1N4t1uk"
                sheet_name = Sheet
                sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)

                if page == "Add Home Expense":
                    target_cols = ["H", "I", "J", "K"]
                elif page == "Add Personal Expense":
                    target_cols = ["B", "C", "D", "E"]
                elif page == "Purchase from Reserve":
                    target_cols = ["M", "N", "O", "P"]
                elif page == "Savings":
                    target_cols = ["R", "S", "T", "U"]
                elif page == "Investment":
                    target_cols = ["W", "X", "Y", "Z"]
                

                row = get_next_available_row(sheet, target_cols)
                data_map = {
                    target_cols[0]: (row, formatted_date),
                    target_cols[1]: (row, category),
                    target_cols[2]: (row, expense),
                    target_cols[3]: (row, items),
                }

                inserted_row = insert_mapped_data(sheet, data_map)
                st.success(f"✅ Data inserted successfully into row {inserted_row}.")

        if reset:
            st.session_state.reset_triggered = True
            st.rerun()

    elif page == "Reports":
        st.write("📊 Reports page is under construction.")

elif authentication_status is False:
    st.error("❌ Username/password is incorrect")

elif authentication_status is None:
    st.info("🔐 Please enter your username and password")
