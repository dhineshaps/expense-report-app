from datetime import date, datetime
import calendar

# Get today's date
today = date.today()

# Get total days in the current month
_, total_days_in_month = calendar.monthrange(today.year, today.month)

# Days remaining including today
days_remaining = total_days_in_month - today.day

print(f"Today's date: {today}")
print(f"Days remaining in the month: {days_remaining}")