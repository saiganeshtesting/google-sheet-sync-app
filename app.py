from fastapi import FastAPI
from gsheet_sync import run_sync

app = FastAPI()

@app.get("/")
def root():
    return {"status": "✅ Service is running."}

@app.get("/sync")
def sync():
    try:
        run_sync()
        return {"status": "✅ Synced successfully"}
    except Exception as e:
        return {"status": "❌ Error", "details": str(e)}
