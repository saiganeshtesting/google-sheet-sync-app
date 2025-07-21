import gspread
from oauth2client.service_account import ServiceAccountCredentials

CENTRAL_SHEET_URL = "https://docs.google.com/spreadsheets/d/1dd6q6fxvCNAGcNWBquJHjB3bccukxMT5pCewZ-3okDc"

def get_gspread_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    return gspread.authorize(creds)

def read_source_urls(config_tab):
    urls = config_tab.col_values(1)[1:]  # Skip header
    return [url for url in urls if url.strip()]

def read_all_data_from_sheets(client, urls):
    all_rows = []
    for url in urls:
        try:
            sheet = client.open_by_url(url)
            first_tab = sheet.get_worksheet(0)
            data = first_tab.get_all_values()
            if data:
                headers = data[0]
                rows = data[1:]
                print(f"✅ Read {len(rows)} rows from: {sheet.title}")
                all_rows.extend(rows)
            else:
                print(f"⚠️ No data found in: {sheet.title}")
        except Exception as e:
            print(f"❌ Error reading {url}: {e}")
    return all_rows

def clear_tab(tab):
    tab.clear()

def update_central_sheet(tab, data):
    if data:
        tab.update(range_name="A2", values=data)
        print(f"✅ Synced {len(data)} rows to Central tab.")
    else:
        print("⚠️ No data to update.")

def main():
    print("📥 Connecting to central sheet...")
    client = get_gspread_client()

    try:
        central_sheet = client.open_by_url(CENTRAL_SHEET_URL)
        print("🔍 Opened:", central_sheet.title)
        print("📄 Tabs:", [ws.title for ws in central_sheet.worksheets()])
        config_tab = central_sheet.worksheet("config")
        central_tab = central_sheet.worksheet("Central")
    except Exception as e:
        print(f"❌ Failed to open central/config/Central tabs: {e}")
        return

    print("🔗 Reading source sheet URLs...")
    source_urls = read_source_urls(config_tab)
    print(f"🔗 Found {len(source_urls)} source sheets.")

    print("📤 Reading data from all source sheets...")
    all_data = read_all_data_from_sheets(client, source_urls)

    print("🧹 Clearing existing data in 'Central' tab...")
    clear_tab(central_tab)

    if all_data:
        print("⬆️ Updating Central tab...")
        update_central_sheet(central_tab, all_data)
    else:
        print("⚠️ No data collected from source sheets.")

if __name__ == "__main__":
    main()
