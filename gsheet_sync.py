import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import os

# Load credentials from Render's secret mount
SERVICE_ACCOUNT_FILE = "/etc/secrets/credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

def sync_sheets():
    # Load the central sheet (with config and Central tab)
    central_url = os.getenv("CENTRAL_SHEET_URL")  # Set this in Render environment
    central_doc = client.open_by_url(central_url)

    config_sheet = central_doc.worksheet("config")
    config_data = config_sheet.get_all_values()[1:]  # Skip header

    all_data = []

    for row in config_data:
        url = row[0]
        try:
            src_doc = client.open_by_url(url)
            for worksheet in src_doc.worksheets():
                df = pd.DataFrame(worksheet.get_all_values())
                if not df.empty:
                    df.columns = df.iloc[0]
                    df = df[1:]
                    all_data.append(df)
        except Exception as e:
            print(f"Failed to load: {url} due to {e}")

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        central_ws = central_doc.worksheet("Central")
        central_ws.clear()
        central_ws.update(
            [final_df.columns.values.tolist()] + final_df.values.tolist()
        )
