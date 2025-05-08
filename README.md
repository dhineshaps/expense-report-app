# expense-report-app
To track the Day to Day expense and Visualize it

# Streamlit Expense Tracker with Google Sheets

A simple, secure, and mobile-friendly expense tracker app built with [Streamlit](https://streamlit.io/) and backed by [Google Sheets](https://www.google.com/sheets/about/) for storing and managing your expense data.

## 🔐 Features

- User authentication with YAML-based credentials (or Streamlit secrets)
- Clean, mobile-friendly UI — no sidebar
- Real-time expense submission to a Google Sheet
- Date picker for easy selection
- Validation to ensure the expense amount is numeric
- Logout functionality
- Easily extendable for dashboards or reporting

## 🛠️ Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/)
- **Backend:** Google Sheets API
- **Auth:** [streamlit-authenticator](https://github.com/mkhorasani/streamlit-authenticator)
- **Secrets Management:** `secrets.toml` (for deployment), `creds.yml` (for local dev)
