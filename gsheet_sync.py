import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_gspread_client():
    encoded = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if not encoded:
        raise ValueError("Missing GOOGLE_APPLICATION_CREDENTIALS_JSON env var")

    credentials_dict = json.loads(encoded)
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    return client

def run_sync():
    client = get_gspread_client()

    # config tab: list of source sheet URLs
    central_sheet = client.open("Central Sheet")  # change this if your sheet name is different
    config_tab = central_sheet.worksheet("config")
    urls = config_tab.col_values(1)[1:]  # Skip header

    central_tab = central_sheet.worksheet("Central")
    all_data = []

    for url in urls:
        try:
            sheet = client.open_by_url(url)
            for worksheet in sheet.worksheets():
                rows = worksheet.get_all_values()
                if not rows:
                    continue
                headers = rows[0]
                for row in rows[1:]:
                    row_data = dict(zip(headers, row))
                    row_data["source_tab"] = f"{sheet.title} - {worksheet.title}"
                    all_data.append(row_data)
        except Exception as e:
            print(f"Error processing sheet {url}: {e}")

    if all_data:
        headers = list(all_data[0].keys())
        values = [headers] + [[row.get(h, "") for h in headers] for row in all_data]
        central_tab.clear()
        central_tab.update("A1", values)
