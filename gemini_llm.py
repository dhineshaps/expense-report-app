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

load_dotenv()



genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

model = genai.GenerativeModel("gemini-1.5-flash-latest")


def analyze_home_expenses(df_home,home_exp_cat,total_spent,allocation):
    prompt = f"""
    You are a household expense advisor.

    Below is the summary of home expenses this month, categorized and grouped:

    Category-wise Spending:
    {home_exp_cat.to_markdown(index=False)}

    Below is the detailed list of items purchased on each day. You can use this to identify patterns or unnecessary/repeated spending:

    Itemized Purchase Log:
    {df_home.to_markdown(index=False)}

    f"The total allocated budget is{allocation}" and total spent is {total_spent}"

    Please:
    1. Point out categories consuming high budget.
    2. Use the itemized log to identify unnecessary or repeated items.
    3. Suggest how to reduce or optimize spending.
    4. Respond in simple language for a middle-class family.
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
5. Suggest any financial optimizations based on patterns in the 'Add-on' notes.

Keep your language simple and clear, as if you're advising a working professional trying to manage monthly personal finances. Avoid repeating values already listed in the summary table.
    """

    response = model.generate_content(prompt)
    return response.text.strip()