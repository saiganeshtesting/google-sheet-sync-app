import gspread
from google.oauth2.service_account import Credentials
import os
from collections import defaultdict

def main():
    # Load service account credentials
    creds_path = os.environ.get("GOOGLE_CREDS_FILE", "credentials.json")
    creds = Credentials.from_service_account_file(creds_path, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    client = gspread.authorize(creds)

    # Open central sheet
    central_sheet_url = os.environ.get("CENTRAL_SHEET_URL")
    central_sheet = client.open_by_url(central_sheet_url)

    config_tab = central_sheet.worksheet("config")
    urls = config_tab.col_values(1)[1:]  # Skip header row

    # Dictionary to group tabs by header row
    grouped_data = defaultdict(list)

    for url in urls:
        try:
            source_sheet = client.open_by_url(url)
            for tab in source_sheet.worksheets():
                values = tab.get_all_values()
                if not values or not values[0]:
                    continue  # skip empty tab

                header_row = tuple(values[0])  # use tuple to make it hashable
                grouped_data[header_row].extend(values[1:])  # exclude header row
        except Exception as e:
            print(f"Error processing {url}: {e}")

    # Write to central sheet grouped by header
    for header, rows in grouped_data.items():
        tab_name = "Tab_" + str(abs(hash(header)) % 10000)  # short hash as tab name
        try:
            worksheet = central_sheet.worksheet(tab_name)
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            worksheet = central_sheet.add_worksheet(title=tab_name, rows="1000", cols="50")

        # Update with headers + combined rows
        worksheet.update([list(header)] + rows)
