import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

st.set_page_config(page_title="Expense Tracker", layout="wide")

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
    .stApp {
        padding-bottom: 60px;
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

def display_expense_report(report_func, *args, date_col, cat_col, amt_col, item_col, 
                           day_title, cat_title, no_data_msg):
    report = report_func(*args, date_col, cat_col, amt_col, item_col, "Date", "Category", "Expense", "Items")
    if report:
        daily_exp, cat_exp = report

        if not daily_exp.empty:
            with st.expander(f"View the {day_title}"):
                st.dataframe(daily_exp, use_container_width=True)

        if not cat_exp.empty:
            with st.expander(f"View 💰 **{cat_title}**"):
                st.dataframe(cat_exp, use_container_width=True)

            fig = px.bar(cat_exp, x="Category", y="Expense", text="Expense", color="Category",
                         title="Expenses by Category", labels={"Expense": "₹ Amount", "Category": "Expense Type"})
            fig.update_traces(texttemplate='₹%{text:.2s}', textposition='outside')
            fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No {day_title} data available.")
    else:
        st.info(f"ℹ️ {no_data_msg}")

date_input = date.today()
date1 = date_input.strftime("%d-%m-%Y")
Mon = int(date1.split("-")[1])
yr = int(date1.split("-")[2])
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "July", "Aug", "Sep", "Oct", "Nov", "Dec"]
Month = month_names[Mon - 1]
Sheet = f"{Month}_{yr}"

@st.cache_resource
def get_gspread_client(sheet_name):
    creds_dict = st.secrets["connections"]["expense"]
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    spreadsheet_id = st.secrets["sheet_id"]
    return client.open_by_key(spreadsheet_id).worksheet(sheet_name)

def get_next_available_row(sheet, column_letters, start_row=2):
    max_row = start_row
    for col_letter in column_letters:
        col_index = ord(col_letter.upper()) - 64
        values = sheet.col_values(col_index)
        last_filled = next((i for i, v in reversed(list(enumerate(values, start=1))) if v.strip()), 0)
        if last_filled + 1 > max_row:
            max_row = last_filled + 1
    return max_row

def insert_mapped_data(sheet, data_map):
    for col, (r, val) in data_map.items():
        sheet.update_acell(f"{col}{r}", val)
    return r

if authentication_status:
    st.success(f"👋 Welcome, {name}!")
    authenticator.logout('Logout', 'main')

    page = st.radio("Go to", ["Add Home Expense", "Add Personal Expense", "Purchase from Reserve",
                               "Savings", "Investment", "Reports"], horizontal=True)

    if page in ["Add Home Expense", "Add Personal Expense", "Purchase from Reserve", "Savings", "Investment"]:
        if page == "Add Personal Expense":
            st.write("Dhinesh's Personal Expenses Only")

        with st.form("expense_form"):
            st.subheader("Enter Expense Details")
            date_input = st.date_input("📅 Date", value=st.session_state.get("date_input", date.today()), key="date_input")
            formatted_date = date_input.strftime("%d-%m-%Y")

            if page == "Add Home Expense":
                category = st.selectbox("📂 Category", ("Grocery", "Vegetables", "Fruits", "Gas", "Cab", "Snacks", "Entertainment",
                                                        "Tickets", "Rent", "Home Maint", "Tea and Snacks", "Food", "Non-Veg",
                                                        "Egg", "Personal wellness", "Others"), key="category_input")
            elif page == "Add Personal Expense":
                category = st.selectbox("📂 Category", ("EMI", "Dad", "Vijaya", "Tea and Snacks", "Fruits", "Cab", "Snacks",
                                                        "Home Snacks", "Home Spend", "Entertainment", "Juice", "Donation", "Tickets",
                                                        "Lent", "Loan Repayment", "Home Maint", "Food", "Non-Veg", "Egg",
                                                        "Personal wellness", "Ecommerce", "Others"), key="category_input")
            elif page == "Purchase from Reserve":
                category = st.selectbox("📂 Category", ("Donation", "Lent", "Loan Repayment", "Home Maint", "Personal wellness",
                                                        "Ecommerce", "Others", "Gift", "Electronics", "Furniture"), key="category_input")
            elif page == "Savings":
                category = st.selectbox("📂 Category", ("Last Month Pass Over", "Gift", "Others"), key="category_input")
            elif page == "Investment":
                category = st.selectbox("📂 Category", ("Gold", "Equity", "Bonds", "Mutual Funds"), key="category_input")

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
                sheet = get_gspread_client(Sheet)
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
        st.subheader("📊 Monthly Report Viewer")

        def report_Datav1(sheetNo, col1, col2, col3, col4, colname1, colname2, colname3, colname4):   
            sheet = get_gspread_client(Sheet)
            col_1 = sheet.col_values(col1)[sheetNo - 1:]
            col_2 = sheet.col_values(col2)[sheetNo - 1:]
            col_3 = sheet.col_values(col3)[sheetNo - 1:]
            col_4 = sheet.col_values(col4)[sheetNo - 1:]
            data = list(zip(col_1, col_2, col_3, col_4)) 

            if data:
                df = pd.DataFrame(data, columns=[colname1, colname2, colname3, colname4])
                df[colname3] = pd.to_numeric(df[colname3], errors='coerce').fillna(0)
                df.index += 1
                grouped = df.groupby(colname2)
                sum_df = grouped[colname3].sum().reset_index()
                sum_df.index += 1
                return df, sum_df
            else:
                return pd.DataFrame(), pd.DataFrame()

        # --- Reports Section ---
        display_expense_report(
            report_Datav1,
            8, 8, 9, 10, 11,
            date_col="Date",
            cat_col="Category",
            amt_col="Expense",
            item_col="Items",
            day_title="Day to Day Expense",
            cat_title="Expense by Category",
            no_data_msg="No data found in the selected range for Home Expense."
        )

        if username == "dhinesh":
            display_expense_report(
                report_Datav1,
                7, 2, 3, 4, 5,
                date_col="Date",
                cat_col="Category",
                amt_col="Expense",
                item_col="Items",
                day_title="Personal Day to Day Expense",
                cat_title="Expense by Category for Personal",
                no_data_msg="No data found in the selected range for Personal Expense."
            )

            display_expense_report(
                report_Datav1,
                7, 13, 14, 15, 16,
                date_col="Date",
                cat_col="Category",
                amt_col="Expense",
                item_col="Items",
                day_title="Reserve Expense",
                cat_title="Expense by Category for Reserve Expense",
                no_data_msg="No data found in the selected range for Reserve Expense."
            )

            display_expense_report(
                report_Datav1,
                7, 23, 24, 25, 26,
                date_col="Date",
                cat_col="Category",
                amt_col="Investment",
                item_col="Instrument",
                day_title="Investments Made",
                cat_title="Total Investments by Category",
                no_data_msg="No data found in the selected range for Investment."
            )

elif authentication_status is False:
    st.error("❌ Username/password is incorrect")

elif authentication_status is None:
    st.info("🔐 Please enter your username and password")
