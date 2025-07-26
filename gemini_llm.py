from dotenv import load_dotenv
import os
import json
import google.generativeai as genai
from email.message import EmailMessage
import base64
import re
import textwrap
from email.mime.multipart import MIMEMultipart
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import streamlit as st
from datetime import date, datetime
import calendar


load_dotenv()



genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

model = genai.GenerativeModel("gemini-1.5-flash-latest")


def analyze_home_expenses(df_home,home_exp_cat,total_spent,allocation):

    today = date.today()

    _, total_days_in_month = calendar.monthrange(today.year, today.month)

    days_remaining = total_days_in_month - today.day

    available_fund = allocation - total_spent

    prompt = f"""
    You are a household expense advisor.

    Below is the summary of home expenses this month, categorized and grouped:

    Category-wise Spending:
    {home_exp_cat.to_markdown(index=False)}

    Budget Overview:
    - Total allocated budget: ₹{allocation}
    - Total spent so far: ₹{total_spent}
    - Remaining budget: ₹{allocation - total_spent}
    - Today's date: {today}
    - Days left in this month: {days_remaining}


    Below is the detailed list of items purchased on each day. You can use this to identify patterns or unnecessary/repeated spending:

    Itemized Purchase Log:
    {df_home.to_markdown(index=False)}

    Please:
    1. Point out categories consuming high budget.
    2. Use the itemized log to identify unnecessary or repeated items.
    3. Suggest how to reduce or optimize spending.
    4. Recommend how to best utilize the remaining ₹{available_fund} over the next {days_remaining} days. Suggest any daily limits if possible
    5. Respond in simple language for a middle-class family.


    **Note:** If an item is perishable (e.g., milk, vegetables, fruits, eggs), do not include it in optimization or cost-reduction suggestions. These are considered essential and non-negotiable.
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def analyze_personal_expenses(personal_exp,personal_exp_cat,Total_Expense):
    prompt = f"""
You are a financial advisor helping an individual manage personal expenses. Below are two tables:

---

### Summary of Expenses:
The first table is grouped by category, showing the total amount spent in each.

{personal_exp_cat.to_markdown(index=False)}

---

### Detailed Expense Entries:
The second table contains raw personal expense entries, with add-on details that can help you find spending patterns.

{personal_exp.to_markdown(index=False)}

---

### Please perform the following analysis:

1. Break down how much is spent in each major category.
2. Highlight any unusually high expenses or recurring large transfers (e.g., EMIs, loans).
3. Identify small but frequent expenses that could be optimized (like snacks, grooming, etc.).
4. Spot any repayment patterns, personal transfers, or luxury purchases.
5. **Check if there are any entries related to investments (e.g., mutual funds, SIPs, stocks, gold, insurance premiums, PPF). If none are found, suggest investment opportunities based on the expense behavior.**
6. Suggest any financial optimizations based on patterns in the 'Add-on' notes.

Keep your language simple and clear, as if you're advising a working professional trying to manage monthly personal finances. Avoid repeating values already listed in the summary table.
    """

    response = model.generate_content(prompt)
    return response.text.strip()