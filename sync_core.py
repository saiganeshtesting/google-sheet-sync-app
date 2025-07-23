import gspread
from google.oauth2.service_account import Credentials
import os
import base64

def save_credentials_from_env():
    b64_creds = os.environ.get("GOOGLE_CREDS_BASE64")
    if not b64_creds:
        raise ValueError("GOOGLE_CREDS_BASE64 not found in environment variables")
    
    creds_json = base64.b64decode(b64_creds).decode("utf-8")
    with open("/tmp/credentials.json", "w") as f:
        f.write(creds_json)
    return "/tmp/credentials.json"

def main():
    creds_path = save_credentials_from_env()
    creds = Credentials.from_service_account_file(creds_path, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    client = gspread.authorize(creds)

    config_sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1i_Bu6s3of9KLRVYYlevq0RQqAEvfCoGk5OiukfoFMGQ")
    config_tab = config_sheet.worksheet("config")
    central_tab = config_sheet.worksheet("Central")

    urls = config_tab.col_values(1)[1:]
    all_rows = []
    for url in urls:
        try:
            sheet = client.open_by_url(url)
            for ws in sheet.worksheets():
                data = ws.get_all_values()
                if data:
                    all_rows.extend(data[1:])  # skip headers
        except Exception as e:
            print(f"Error reading {url}: {e}")

    central_tab.clear()
    if all_rows:
        headers = ["Domain", "Client", "Location", "Email", "Phone Number", "Job Type", "Full JD"]
        central_tab.update([headers] + all_rows)
