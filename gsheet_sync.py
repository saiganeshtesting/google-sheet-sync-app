import gspread
from oauth2client.service_account import ServiceAccountCredentials

def run_sync():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)

    # Read URLs from 'config' tab of your central sheet
    central_sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/YOUR_CENTRAL_SHEET_ID")
    config = central_sheet.worksheet("config")
    urls = [row[0] for row in config.get_all_values()[1:] if row]

    central_ws = central_sheet.worksheet("Central")
    combined_data = []

    for url in urls:
        try:
            sheet = client.open_by_url(url)
            for ws in sheet.worksheets():
                data = ws.get_all_values()
                if data:
                    combined_data.extend(data[1:] if data[0] == combined_data[0] else data)
        except Exception as e:
            print(f"Skipping {url}: {e}")
            continue

    if combined_data:
        central_ws.clear()
        central_ws.update("A1", combined_data)
