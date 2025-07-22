import gspread
from google.oauth2.service_account import Credentials
import time
import hashlib
import os
import sys

# --------------------------
# AUTH SETUP
# --------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "/var/render/secrets/service_account.json")
DELAY_BETWEEN_CALLS = 3  # seconds

creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)

# --------------------------
# UTILS
# --------------------------
def hash_header_row(row):
    return hashlib.sha256("||".join(row).encode()).hexdigest()

# --------------------------
# STEP 1: Get central sheet from env
# --------------------------
def load_config_sheet():
    config_sheet_url = os.environ.get("CENTRAL_SHEET_URL")
    if not config_sheet_url:
        print("❌ Environment variable CENTRAL_SHEET_URL is not set.")
        sys.exit(1)

    print("📥 Connecting to central sheet...")
    try:
        sheet = gc.open_by_url(config_sheet_url)
        config_ws = sheet.worksheet("config")
        urls = config_ws.col_values(1)[1:]  # skip header
        return sheet, urls
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return None, []

# --------------------------
# STEP 2: Read all data from all tabs of all source sheets
# Group them by header row
# --------------------------
def collect_data_by_header(sheets_urls):
    grouped_data = {}  # { header_hash: {"header": [], "rows": [] } }

    for url in sheets_urls:
        try:
            print(f"🔗 Reading {url}")
            ss = gc.open_by_url(url)
            for ws in ss.worksheets():
                rows = ws.get_all_values()
                if not rows or not rows[0]:
                    continue
                header = rows[0]
                data_rows = rows[1:]

                header_hash = hash_header_row(header)
                if header_hash not in grouped_data:
                    grouped_data[header_hash] = {"header": header, "rows": []}
                grouped_data[header_hash]["rows"].extend(data_rows)

                time.sleep(DELAY_BETWEEN_CALLS)
        except Exception as e:
            print(f"⚠️ Error reading {url}: {e}")
            continue
    return grouped_data

# --------------------------
# STEP 3: Write grouped data to central sheet
# --------------------------
def write_to_central_sheet(central_sheet, grouped_data):
    print("📤 Writing to central sheet...")
    for idx, (header_hash, group) in enumerate(grouped_data.items(), start=1):
        sheet_name = f"tab_{idx}"
        try:
            try:
                ws = central_sheet.worksheet(sheet_name)
                ws.clear()
            except gspread.exceptions.WorksheetNotFound:
                ws = central_sheet.add_worksheet(title=sheet_name, rows="1000", cols="50")

            ws.update([group["header"]] + group["rows"])
            print(f"✅ Updated {sheet_name}")
            time.sleep(DELAY_BETWEEN_CALLS)
        except Exception as e:
            print(f"❌ Failed to write {sheet_name}: {e}")

# --------------------------
# MAIN
# --------------------------
if __name__ == "__main__":
    central_sheet, sheet_urls = load_config_sheet()
    if not central_sheet:
        exit(1)

    data_by_header = collect_data_by_header(sheet_urls)
    write_to_central_sheet(central_sheet, data_by_header)
