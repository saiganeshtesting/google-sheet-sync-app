import os
import json
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def run_sync():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    encoded = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if not encoded:
        raise Exception("Missing GOOGLE_APPLICATION_CREDENTIALS_JSON env var")

    creds_dict = json.loads(base64.b64decode(encoded).decode("utf-8"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    config_url = os.getenv("CONFIG_SHEET_URL")
    if not config_url:
        raise Exception("Missing CONFIG_SHEET_URL env var")

    sheet = client.open_by_url(config_url)
    worksheet = sheet.worksheet("config")
    data = worksheet.get_all_values()

    print("✅ Synced data from config:")
    for row in data:
        print(row)
