import gspread
from google.oauth2.service_account import Credentials
import os
import base64
import json
from collections import defaultdict

def get_credentials_from_env():
    """
    Reads GOOGLE_CREDS_BASE64 from environment, decodes, and returns Credentials object.
    """
    encoded = os.environ.get("GOOGLE_CREDS_BASE64")
    if not encoded:
        raise ValueError("GOOGLE_CREDS_BASE64 environment variable not set")

    decoded = base64.b64decode(encoded)
    creds_json = json.loads(decoded)
    creds = Credentials.from_service_account_info(creds_json, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return creds

def main():
    creds = get_credentials_from_env()
    client = gspread.authorize(creds)

    # Load central sheet
    central_sheet_url = os.environ.get("CENTRAL_SHEET_URL")
    central_sheet = client.open_by_url(central_sheet_url)

    config_tab = central_sheet.worksheet("config")
    urls = config_tab.col_values(1)[1:]  # Skip header row

    grouped_data = defaultdict(list)

    for url in urls:
        try:
            source_sheet = client.open_by_url(url)
            for tab in source_sheet.worksheets():
                values = tab.get_all_values()
                if not values or not values[0]:
                    continue  # skip empty tabs

                header_row = tuple(values[0])
                grouped_data[header_row].extend(values[1:])
        except Exception as e:
            print(f"Error processing {url}: {e}")

    # Write data grouped by header into separate tabs
    for header, rows in grouped_data.items():
        tab_name = "Tab_" + str(abs(hash(header)) % 10000)  # generate tab name from header hash
        try:
            worksheet = central_sheet.worksheet(tab_name)
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            worksheet = central_sheet.add_worksheet(title=tab_name, rows="1000", cols="50")

        worksheet.update([list(header)] + rows)

if __name__ == "__main__":
    main()
