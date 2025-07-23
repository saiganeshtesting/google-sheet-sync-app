# sync_core.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import hashlib
import time
import random
import os
import json
import base64
from flask import Flask, request

app = Flask(__name__)

# Setup
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
CENTRAL_SHEET_URL = "https://docs.google.com/spreadsheets/d/1i_Bu6s3of9KLRVYYlevq0RQqAEvfCoGk5OiukfoFMGQ"

# Decode credentials from environment
def get_gspread_client():
    b64_creds = os.environ.get("GOOGLE_CREDS_B64")
    if not b64_creds:
        raise Exception("Missing GOOGLE_CREDS_B64 env var")
    creds_dict = json.loads(base64.b64decode(b64_creds).decode("utf-8"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    return gspread.authorize(creds)

# Retry decorator
def retry_on_rate_limit(func):
    def wrapper(*args, **kwargs):
        max_retries = 5
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except gspread.exceptions.APIError as e:
                if "Quota exceeded" in str(e):
                    wait_time = 5 + attempt * 5 + random.uniform(1, 3)
                    print(f"⏳ Rate limit hit. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    raise
        raise Exception("❌ Too many retries. API quota exceeded.")
    return wrapper

@retry_on_rate_limit
def get_sheet_by_url(client, url):
    return client.open_by_url(url)

@retry_on_rate_limit
def get_all_values(worksheet):
    return worksheet.get_all_values()

def get_all_source_sheet_urls(config_sheet):
    try:
        urls = config_sheet.col_values(1)[1:]
        return [url.strip() for url in urls if url.strip()]
    except Exception as e:
        print("❌ Error reading config sheet:", e)
        return []

def normalize_header(header_row):
    norm = '|'.join(cell.strip() for cell in header_row)
    hash_key = hashlib.md5(norm.encode()).hexdigest()[:6]
    return norm, hash_key

def extract_all_tabs(client, sheet_url):
    grouped_data = {}
    try:
        sheet = get_sheet_by_url(client, sheet_url)
        for worksheet in sheet.worksheets():
            time.sleep(1.2)
            data = get_all_values(worksheet)
            if not data or not data[0]:
                continue
            header, hash_key = normalize_header(data[0])
            if hash_key not in grouped_data:
                grouped_data[hash_key] = {
                    "header": data[0],
                    "rows": []
                }
            grouped_data[hash_key]["rows"].extend(data[1:])
        print(f"✅ Processed: {sheet.title}")
    except Exception as e:
        print(f"❌ Error reading {sheet_url}: {e}")
    return grouped_data

def run_sync():
    print("📥 Connecting to central sheet...")
    client = get_gspread_client()

    try:
        central_sheet = get_sheet_by_url(client, CENTRAL_SHEET_URL)
        config_tab = central_sheet.worksheet("config")
    except Exception as e:
        print("❌ Failed to open central/config tab:", e)
        return "Failed"

    print("🔗 Reading source sheet URLs...")
    sheet_urls = get_all_source_sheet_urls(config_tab)

    header_map = {}
    for url in sheet_urls:
        grouped = extract_all_tabs(client, url)
        for key, content in grouped.items():
            if key not in header_map:
                header_map[key] = {
                    "header": content["header"],
                    "rows": []
                }
            header_map[key]["rows"].extend(content["rows"])

    print("📤 Updating central sheet...")
    for idx, (key, content) in enumerate(header_map.items(), 1):
        tab_name = f"tab{idx}"
        try:
            try:
                worksheet = central_sheet.worksheet(tab_name)
                worksheet.clear()
            except gspread.exceptions.WorksheetNotFound:
                worksheet = central_sheet.add_worksheet(title=tab_name, rows="1000", cols="50")

            final_data = [content["header"]] + content["rows"]
            worksheet.update('A1', final_data)
            print(f"✅ Updated {tab_name} with {len(content['rows'])} rows")
        except Exception as e:
            print(f"❌ Failed to update {tab_name}: {e}")

    return "Success"

# HTTP Endpoint for Render
@app.route("/sync", methods=["POST"])
def sync_endpoint():
    result = run_sync()
    return {"status": result}, 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
