import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from collections import defaultdict

def run_sync():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    central_sheet = client.open("Central Sheet Name")  # replace with your actual sheet name
    config_ws = central_sheet.worksheet("config")
    sheet_urls = [row[0] for row in config_ws.get_all_values() if row]

    header_groups = defaultdict(list)

    for url in sheet_urls:
        sheet = client.open_by_url(url)
        for ws in sheet.worksheets():
            data = ws.get_all_values()
            if not data:
                continue
            header = tuple(data[0])
            df = pd.DataFrame(data[1:], columns=header)
            header_groups[header].append(df)

    for header, dfs in header_groups.items():
        combined_df = pd.concat(dfs, ignore_index=True)
        tab_name = header[0][:30]
        try:
            ws = central_sheet.worksheet(tab_name)
            central_sheet.del_worksheet(ws)
        except:
            pass
        new_ws = central_sheet.add_worksheet(title=tab_name, rows=1000, cols=30)
        new_ws.update([list(header)] + combined_df.values.tolist())
