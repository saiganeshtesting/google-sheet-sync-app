from dotenv import load_dotenv
import os
import gspread
from utils import group_data_by_headers
load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
CENTRAL_SHEET_URL = os.getenv("CENTRAL_SHEET_URL")

gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)

def get_configured_urls(sheet):
    try:
        config_tab = sheet.worksheet("config")
        urls = config_tab.col_values(1)[1:]  # Skip header
        return [url.strip() for url in urls if url.strip()]
    except Exception as e:
        print(f"❌ Failed to read config tab: {e}")
        return []

def main():
    print("📥 Connecting to central sheet...")
    try:
        central_sheet = gc.open_by_url(CENTRAL_SHEET_URL)
        source_urls = get_configured_urls(central_sheet)

        all_data = {}  # header_key: [rows]

        for url in source_urls:
            try:
                src = gc.open_by_url(url)
                for ws in src.worksheets():
                    records = ws.get_all_values()
                    if not records or len(records[0]) == 0:
                        continue
                    header = records[0]
                    key = "|".join(header).strip()
                    all_data.setdefault(key, []).extend(records[1:])
            except Exception as e:
                print(f"⚠️ Skipping {url}: {e}")

        for header_key, rows in all_data.items():
            sheet_title = f"Tab_{abs(hash(header_key)) % 100000}"  # Consistent name
            try:
                try:
                    ws = central_sheet.worksheet(sheet_title)
                    existing_data = ws.get_all_values()
                    current_data = [header_key.split("|")] + rows
                    if existing_data[0] != current_data[0]:  # Header mismatch
                        ws.clear()
                    ws.clear()
                    ws.update(current_data)
                except gspread.exceptions.WorksheetNotFound:
                    ws = central_sheet.add_worksheet(title=sheet_title, rows=1000, cols=50)
                    ws.update([header_key.split("|")] + rows)
            except Exception as e:
                print(f"❌ Failed updating central tab {sheet_title}: {e}")

    except Exception as e:
        print(f"❌ Failed to open central sheet: {e}")

if __name__ == "__main__":
    main()
