import os
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, request

app = Flask(__name__)

# Load credentials from JSON file
SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

gc = gspread.authorize(credentials)

# Central Sheet URL (replace this with your own central sheet)
CENTRAL_SHEET_URL = "https://docs.google.com/spreadsheets/d/1i_Bu6s3of9KLRVYYlevq0RQqAEvfCoGk5OiukfoFMGQ/edit?gid=0#gid=0"

def get_headers(worksheet):
    headers = worksheet.row_values(1)
    return [header.strip() for header in headers]

def get_config_sheet_urls():
    central_sheet = gc.open_by_url(CENTRAL_SHEET_URL)
    config_ws = central_sheet.worksheet("config")
    urls = config_ws.col_values(1)[1:]  # skip header
    return [url for url in urls if url.strip()]

def clear_worksheet(worksheet):
    worksheet.clear()

def update_or_create_tab(spreadsheet, tab_name, data):
    try:
        worksheet = spreadsheet.worksheet(tab_name)
        clear_worksheet(worksheet)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=tab_name, rows="100", cols="20")

    if data:
        worksheet.update("A1", data)

def match_and_group_data_by_headers(source_data, source_headers, tab_map):
    matched_tab = None
    for tab_name, tab_headers in tab_map.items():
        if source_headers == tab_headers:
            matched_tab = tab_name
            break
    return matched_tab

def run_sync():
    central_sheet = gc.open_by_url(CENTRAL_SHEET_URL)
    urls = get_config_sheet_urls()

    # Get existing tabs and their headers
    tab_map = {}
    for worksheet in central_sheet.worksheets():
        headers = get_headers(worksheet)
        tab_map[worksheet.title] = headers

    for url in urls:
        try:
            sheet = gc.open_by_url(url)
            for worksheet in sheet.worksheets():
                data = worksheet.get_all_values()
                if not data:
                    continue
                headers = [header.strip() for header in data[0]]
                matched_tab = match_and_group_data_by_headers(data, headers, tab_map)

                if matched_tab:
                    existing_data = central_sheet.worksheet(matched_tab).get_all_values()
                    combined_data = existing_data + data[1:]
                    update_or_create_tab(central_sheet, matched_tab, combined_data)
                else:
                    tab_name = f"{sheet.title[:10]}_{worksheet.title[:10]}"
                    update_or_create_tab(central_sheet, tab_name, data)
                    tab_map[tab_name] = headers

        except Exception as e:
            print(f"Error syncing sheet {url}: {e}")

    return "✅ Sync complete"

# Home route for Render check
@app.route("/", methods=["GET"])
def home():
    return {
        "message": "✅ Google Sheets Sync API is live! Use GET or POST /sync"
    }

# Sync endpoint supports both GET and POST
@app.route("/sync", methods=["GET", "POST"])
def sync_endpoint():
    if request.method == "GET":
        return {
            "message": "✅ /sync is ready. Use POST to trigger sync."
        }
    result = run_sync()
    return {"status": result}, 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
