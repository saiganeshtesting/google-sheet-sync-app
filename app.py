from fastapi import FastAPI
from fastapi.responses import JSONResponse
from gsheet_sync import sync_sheets

app = FastAPI()

@app.get("/")
def root():
    return {"message": "✅ Google Sheet Sync App is live"}

@app.get("/sync")
def sync():
    try:
        sync_sheets()
        return JSONResponse(content={"status": "✅ Synced successfully"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
