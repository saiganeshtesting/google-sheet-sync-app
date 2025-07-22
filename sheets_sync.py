import gspread
from google.oauth2.service_account import Credentials
from collections import defaultdict
import hashlib

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_gspread_client():
    creds = Credentials.from_service_account_info(json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"]), scopes=SCOPES)
    return gspread.authorize(creds)

def get_sheet_by_url(gc, url):
    try:
        return gc.open_by_url(url)
    except Exception as e:
        print(f"❌ Error opening {url}: {e}")
        return None

def hash_header(header_row):
    return hashlib.sha256(','.join(header_row).encode()).hexdigest()

def sync_data():
    gc = get_gspread_client()
    central_url = "https://docs.google.com/spreadsheets/d/1dd6q6fxvCNAGcNWBquJHjB3bccukxMT5pCewZ-3okDc/edit?gid=0#gid=0"
    central_sheet = get_sheet_by_url(gc, central_url)
    if not central_sheet:
        return "❌ Could not open central sheet."

    try:
        config_ws = central_sheet.worksheet("config")
    except Exception as e:
        return f"❌ Missing 'config' tab in central sheet: {e}"

    try:
        source_urls = config_ws.col_values(1)[1:]  # skip header
    except Exception as e:
        return f"❌ Couldn't read source sheet URLs: {e}"

    merged_data = defaultdict(list)
    header_map = {}

    for url in source_urls:
        sheet = get_sheet_by_url(gc, url)
        if not sheet:
            continue

        for ws in sheet.worksheets():
            values = ws.get_all_values()
            if not values or not values[0]:
                continue

            header = values[0]
            h_hash = hash_header(header)

            if h_hash not in header_map:
                tab_name = f"group_{len(header_map)+1}"
                header_map[h_hash] = (tab_name, header)
            else:
                tab_name, _ = header_map[h_hash]

            merged_data[tab_name].extend(values[1:])  # skip header

    for tab_name, rows in merged_data.items():
        try:
            ws = central_sheet.worksheet(tab_name)
            ws.clear()
        except gspread.exceptions.WorksheetNotFound:
            ws = central_sheet.add_worksheet(title=tab_name, rows="1000", cols="30")

        header = header_map[[k for k, v in header_map.items() if v[0] == tab_name][0]][1]
        ws.update([header] + rows)

    return "✅ Sync completed successfully!"
