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
from gspread.exceptions import WorksheetNotFound
import sys
from gemini_llm import analyze_home_expenses,analyze_personal_expenses

st.set_page_config(page_title="Expense Tracker", layout="wide")


if "reset_triggered" in st.session_state and st.session_state.reset_triggered:
    st.session_state.expense_input = ""
    st.session_state.items_input = ""
    st.session_state.category_input = "Grocery"
    st.session_state.date_input = date.today()
    st.session_state.reset_triggered = False
    st.rerun()



#Initialize session state values to avoid KeyErrors
# defaults = {
#     "reset_triggered": False,
#     "expense_input": "",
#     "items_input": "",
#     "category_input": "Grocery",
#     "date_input": date.today()
# }

# for key, val in defaults.items():
#     if key not in st.session_state:
#         st.session_state[key] = val
		
# if "reset_triggered" in st.session_state and st.session_state.reset_triggered:
#     st.session_state.expense_input = ""
#     st.session_state.items_input = ""
#     st.session_state.category_input = ""
#     st.session_state.date_input = date.today()
#     st.session_state.reset_triggered = False
#     st.rerun()

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

config = yaml.safe_load(st.secrets["auth"]["config"])
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

######################### added to handle the session state ##########################################
# defaults = {
#     "reset_triggered": False,
#     "expense_input": "",
#     "items_input": "",
#     "category_input": "",  # <- empty so page can set it contextually
#     "date_input": date.today()
# }

# for key, val in defaults.items():
#     if key not in st.session_state:
#         st.session_state[key] = val
######################### added to handle the session state ##########################################

st.title("📒 Expense Tracker")
name, authentication_status, username = authenticator.login('Login', 'main')

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
    return client.open_by_key(spreadsheet_id)
    #return client.open_by_key(spreadsheet_id).worksheet(sheet_name)

def set_header_colors(worksheet):
    sheet_id = worksheet._properties.get("sheetId")
    color_groups = [
        (0, 4, {"red": 0.9, "green": 0.9, "blue": 0.9}),   # Group 1: Income
        (6, 10, {"red": 0.8, "green": 0.93, "blue": 0.8}),  # Group 2: Allocation
        (12, 15, {"red": 0.8, "green": 0.85, "blue": 1.0}), # Group 3: Purchase from Reserve
        (17, 20, {"red": 1.0, "green": 0.9, "blue": 0.8}),  # Group 4: Reserve
        (22, 25, {"red": 1.0, "green": 1.0, "blue": 0.8})   # Group 5: Investment
    ]

    requests = []

    for start_col, end_col, color in color_groups:
        requests.append({
            "updateCells": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 5,  # Row 6 (0-based index)
                    "endRowIndex": 6,
                    "startColumnIndex": start_col,
                    "endColumnIndex": end_col + 1  # include end column
                },
                "rows": [
                    {
                        "values": [
                            {
                                "userEnteredFormat": {
                                    "backgroundColor": color
                                }
                            }
                        ] * (end_col - start_col + 1)
                    }
                ],
                "fields": "userEnteredFormat.backgroundColor"
            }
        })

    # Apply color formatting
    worksheet.spreadsheet.batch_update({"requests": requests})

def get_or_create_worksheet(spreadsheet, sheet_name):
    try:
        return spreadsheet.worksheet(sheet_name)
    except WorksheetNotFound:
        st.warning(f"Worksheet '{sheet_name}' not found. Creating it now.")
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="26")
        headers = [
            "Income", "Date", "Expenses", "Amount", "Add-on", "",
            "Allocation", "Date", "Expenses", "Amount", "Items", "",
            "Date", "Purchase from Reserve", "Amount", "Items", "",
            "Date", "Reserve", "Amount", "Item", "",
            "Date", "Investment", "Amout", "Item"
        ]
        cell_range = f"A6:{chr(64 + len(headers))}6"  # chr(64 + 26) = 'Z'
        worksheet.update(cell_range, [headers])
        st.info("Updating the formula")
        worksheet.update_acell('D3', '=SUM(D7:D)')
        worksheet.update_acell('D4', '=MINUS(A7, LEFT(D3, 3))')
        worksheet.update_acell('J3', '=sum(J7:J)')
        worksheet.update_acell('I4', '=MINUS(G7,J3)')
        worksheet.update_acell('O3', '=sum(O7:O)')
        worksheet.update_acell('Y3', '=sum(Y7:Y)')
        worksheet.update_acell('C3', 'Total Expense')
        worksheet.update_acell('C4', 'Available')
        worksheet.update_acell('H3', 'Total Expense')
        worksheet.update_acell('H4', 'Available')
        worksheet.update_acell('N3', 'Total Expense')
        worksheet.update_acell('X3', 'Total Investment')
        st.info("Formulas updated")
        st.info("Formatting") 
        set_header_colors(worksheet)
        st.info("Formatting Completed")
        return worksheet


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
                               "Savings", "Investment", "Reports"], horizontal=False)

    if page in ["Add Home Expense", "Add Personal Expense", "Purchase from Reserve", "Savings", "Investment"]:
        if page == "Add Personal Expense":
            st.write("Dhinesh's Personal Expenses Only")

        with st.form("expense_form"):
            st.subheader("Enter Expense Details")
            date_input = st.date_input("📅 Date", value=st.session_state.get("date_input", date.today()), key="date_input")
            formatted_date = date_input.strftime("%d-%m-%Y")

            if page == "Add Home Expense":
                category = st.selectbox("📂 Category", ("Grocery", "Vegetables", "Fruits", "Gas","Fuel","Dress", "Cab", "Snacks", "Entertainment",
                                                         "Tickets", "Rent", "Home Maint","Wifi", "Tea and Snacks", "Food", "Non-Veg", "Pharmacy",
                                                        "Egg", "Personal wellness","Mobile Recharge", "Others"), key="category_input")
            elif page == "Add Personal Expense":
                category = st.selectbox("📂 Category", ("EMI", "Dad", "Vijaya", "Tea and Snacks", "Fruits", "Cab", "Snacks","ATM Withdrawl",
                                                        "Home Snacks", "Home Spend", "Entertainment", "Juice", "Donation","Home Fuel", "Tickets",
                                                        "Lent", "Loan Repayment", "Home Maint", "Food", "Non-Veg", "Egg","Dress", "Grooming",
                                                        "Pharmacy", "Dental","Mobile Recharge","Personal wellness", "Ecommerce", "Birthday Celebration", 
                                                        "Others"), key="category_input")
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
                #sheet = get_gspread_client(Sheet)
                spreadsheet = get_gspread_client(Sheet)
                sheet = get_or_create_worksheet(spreadsheet, Sheet)

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
            #st.success(f"✅ Data inserted")

        if reset:
            st.session_state.reset_triggered = True
            st.rerun()

    elif page == "Reports":
        st.title("📊 Monthly Report Viewer")
   
        spreadsheet = get_gspread_client(Sheet)
        sheet = get_or_create_worksheet(spreadsheet, Sheet)
        with st.expander(f"{Sheet} Expenses and Investments"):
        #st.subheader(f"{Sheet} Expenses and Investments")
            Total_Expense = sheet.acell('D3').value
            Available_Fund = sheet.acell('D4').value
            Total_Home_Expense = sheet.acell('J3').value
            Available_Home_Expense_Fund = sheet.acell('I4').value
            Allocated_home_fund = sheet.acell('G7').value
            Purchase_From_Reserve = sheet.acell('O3').value
            Investment_Made = sheet.acell('Y3').value
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Total Expense Including Home Expense", value=f"₹{Total_Expense}")
            with col2:
                st.metric(label="Available Fund", value=f"₹{Available_Fund}")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Total Home Expense", value=f"₹{Total_Home_Expense}")
            with col2:
                st.metric(label="Available Home Expense Fund", value=f"₹{Available_Home_Expense_Fund}")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Purchase From Reserve", value=f"₹{Purchase_From_Reserve}")
            with col2:
                st.metric(label="Investment Made", value=f"₹{Investment_Made}")
         


        def report_Data(sheetNo, col1, col2, col3, col4, colname1, colname2, colname3, colname4):   
            #sheet = get_gspread_client(Sheet)
            spreadsheet = get_gspread_client(Sheet)
            sheet = get_or_create_worksheet(spreadsheet, Sheet)
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
                
        st.subheader("🏠 Home Expenses")
        
        home_report = report_Data(7, 8, 9, 10, 11, "Date", "Category", "Expense", "Items")
        if home_report:
            home_exp, home_exp_cat = home_report
        
            if not home_exp.empty:
                with st.expander("View the Day to Day Expense"):
                    st.dataframe(home_exp, use_container_width=True)
        
            if not home_exp_cat.empty:
                with st.expander("View 💰 **Expense by Category**"):
                    st.dataframe(home_exp_cat, use_container_width=True)
                    groc_exp =home_exp_cat[home_exp_cat['Category'].str.lower() == 'grocery']['Expense'].sum()
                    veg_exp =home_exp_cat[home_exp_cat['Category'].str.lower() == 'Vegetables']['Expense'].sum()
                    non_veg_exp =home_exp_cat[home_exp_cat['Category'].str.lower() == 'Non-Veg']['Expense'].sum()
                    tickets_exp =home_exp_cat[home_exp_cat['Category'].str.lower() == 'Tickets']['Expense'].sum()
                    cab_exp =home_exp_cat[home_exp_cat['Category'].str.lower() == 'Cab']['Expense'].sum()
                    entertainment_exp =home_exp_cat[home_exp_cat['Category'].str.lower() == 'Entertainment']['Expense'].sum()
                    eatables_exp =veg_exp+non_veg_exp
                    st.write(groc_exp)
                    st.write(veg_exp)
                    st.write(non_veg_exp)
                    st.write(eatables_exp)
                    st.write(tickets_exp)
                    st.write(cab_exp)
                    st.write(entertainment_exp)
        
                fig = px.bar(home_exp_cat, x="Category", y="Expense", text="Expense", color="Category",
                             title="Home Expenses by Category", labels={"Expense": "₹ Amount", "Category": "Expense Type"})
                fig.update_traces(texttemplate='₹%{text:.2s}', textposition='outside')
                fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No Home Expense data available.")
            Total_Home_Expense=int(Total_Home_Expense)   
            #st.write(analyze_home_expenses(home_exp,home_exp_cat,Total_Home_Expense))
        else:
            st.info("ℹ️ No data found in the selected range for Home Expense.")
        ######################################################################################################
        if username == "dhinesh":
            st.subheader("🧑 Personal Expenses")
            personal_report = report_Data(7, 2, 3, 4, 5, "Date", "Category", "Expense", "Items") 
            if personal_report:
                
                personal_exp, personal_exp_cat = personal_report
            
                if not personal_exp.empty:
                    with st.expander("View the Personal Day to Day Expense"):
                        st.dataframe(personal_exp, use_container_width=True)
            
                if not personal_exp_cat.empty:
                    with st.expander("View 💰 **Expense by Category for Personal**"):
                        st.dataframe(personal_exp_cat, use_container_width=True)
            
                    fig = px.bar(personal_exp_cat, x="Category", y="Expense", text="Expense", color="Category",
                                 title="Personal Expenses by Category", labels={"Expense": "₹ Amount", "Category": "Expense Type"})
                    fig.update_traces(texttemplate='₹%{text:.2s}', textposition='outside')
                    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No Personal Expense data available.")
                Total_Expense = int(Total_Expense)
               # st.markdown(analyze_personal_expenses(personal_exp,personal_exp_cat,Total_Expense))
            else:
                st.info("ℹ️ No data found in the selected range.")
            ##############################AI Report##############################################################

            st.markdown("---")
            st.markdown("### 🧠 Generate AI-Powered Reports")
            st.caption("Click the button below to generate a financial summary based on your expense data.")

            # Centered Button Layout
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                b1, b2 = st.columns(2)

                with b1:
                    home_clicked = st.button("🏡 Home AI Report", type="primary")

                with b2:
                    personal_clicked = st.button("👤 Personal AI Report", type="primary")

            # Trigger Actions
            if home_clicked:
                with st.spinner("Generating Home Report..."):
                    home_summary = analyze_home_expenses(home_exp,home_exp_cat,Total_Home_Expense,Allocated_home_fund)  # Replace with your function
                    st.session_state["home_summary"] = home_summary

            if personal_clicked:
                with st.spinner("Generating Personal Report..."):
                    personal_summary = analyze_personal_expenses(personal_exp,personal_exp_cat,Total_Expense)  # Replace with your function
                    st.session_state["personal_summary"] = personal_summary

            # Expander Sections
            if "home_summary" in st.session_state:
                with st.expander("📘 View Home AI Report"):
                    st.markdown(st.session_state["home_summary"])
                    st.download_button("💾 Download Home Report", st.session_state["home_summary"], file_name="home_ai_report.txt")

            if "personal_summary" in st.session_state:
                with st.expander("📘 View Personal AI Report"):
                    st.markdown(st.session_state["personal_summary"])
                    st.download_button("💾 Download Personal Report", st.session_state["personal_summary"], file_name="personal_ai_report.txt")
            
            # col1, col2 = st.columns(2)

            # with col1:
            #     if st.button("🏡 Generate Home AI Report", type="primary"):
            #         with st.spinner("Analyzing home expenses..."):
            #             st.session_state["home_ai_summary"] = analyze_home_expenses(
            #                 home_exp,home_exp_cat,Total_Home_Expense
            #             )

            # with col2:
            #     if st.button("👤 Generate Personal AI Report", type="primary"):
            #         with st.spinner("Analyzing personal expenses..."):
            #             st.session_state["personal_ai_summary"] = analyze_personal_expenses(
            #                 personal_exp,personal_exp_cat,Total_Expense
            #             )

            # # Display and download Home Report
            # if "home_ai_summary" in st.session_state:
            #     with st.expander("🏡 View Home Expense Report"):
            #         st.markdown(st.session_state["home_ai_summary"])
            #         st.download_button(
            #             "💾 Download Home Report",
            #             st.session_state["home_ai_summary"],
            #             file_name="home_expense_report.txt"
            #         )

            # # Display and download Personal Report
            # if "personal_ai_summary" in st.session_state:
            #     with st.expander("👤 View Personal Expense Report"):
            #         st.markdown(st.session_state["personal_ai_summary"])
            #         st.download_button(
            #             "💾 Download Personal Report",
            #             st.session_state["personal_ai_summary"],
            #             file_name="personal_expense_report.txt"
            #         )

            ######################################################################################################
            st.subheader("🐖💰 Savings")
            savings_report = report_Data(7, 18, 19, 20, 21, "Date", "Category", "Amount", "Items") 
            if savings_report:
            
                savings_data, savings_by_category = savings_report
            
                if not savings_data.empty:
                    with st.expander("View the Day-to-Day Savings"):
                        st.dataframe(savings_data, use_container_width=True)
            
                if not savings_by_category.empty:
                    with st.expander("View 💵 **Savings by Category**"):
                        st.dataframe(savings_by_category, use_container_width=True)
            
                    fig = px.bar(savings_by_category, x="Category", y="Amount", text="Amount", color="Category",
                                 title="Savings by Category", labels={"Amount": "₹ Amount", "Category": "Savings Type"})
                    fig.update_traces(texttemplate='₹%{text:.2s}', textposition='outside')
                    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No Savings data available.")
            else:
                st.info("ℹ️ No data found in the selected range for Savings.")

            ###########################################################################################################    
            st.subheader("💰 Reserve Expense")
            
            reserve_report = report_Data(7, 13, 14, 15, 16, "Date", "Category", "Expense", "Items") 
            if reserve_report:
                reserve_exp, reserve_exp_cat = reserve_report
                if not reserve_exp.empty:
                    with st.expander("View the Reserve Expense"):
                        st.dataframe(reserve_exp, use_container_width=True)

                if not reserve_exp_cat.empty:
                    with st.expander("View 💰 **Expense by Category for Reserve Expense**"):
                        st.dataframe(reserve_exp_cat, use_container_width=True)

                    fig2 = px.bar(reserve_exp_cat, x="Category", y="Expense", text="Expense", color="Category",
                                  title="Reserve Expenses by Category", labels={"Expense": "₹ Amount", "Category": "Expense Type"})
                    fig2.update_traces(texttemplate='₹%{text:.2s}', textposition='outside')
                    fig2.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("No Reserve Expense data available.")
            else:
                st.info("ℹ️ No data found in the selected range.")
            ######################################################################################################
            st.subheader("📈 Investment Spend")
            result = report_Data(7, 23, 24, 25, 26, "Date", "Category", "Investment", "Instrument")
            if result:
                inv_exp, inv_exp_cat = result
                if not inv_exp.empty:
                    with st.expander("View 💰 **Investment Made**"):
                        st.dataframe(inv_exp)
                if not inv_exp_cat.empty:
                    with st.expander("View 💰 **Total Investments by Category**"):
                        st.dataframe(inv_exp_cat)

                    fig3 = px.bar(inv_exp_cat, x="Category", y="Investment", text="Investment", color="Category",
                                  title="Investment Made", labels={"Investment": "₹ Amount", "Category": "Investment Type"})
                    fig3.update_traces(texttemplate='₹%{text:.2s}', textposition='outside')
                    fig3.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.warning("No investment data available.")
            else:
                st.error("Failed to retrieve data.")
             ######################################################################################################
elif authentication_status is False:
    st.error("❌ Username/password is incorrect")

elif authentication_status is None:
    st.info("🔐 Please enter your username and password")
