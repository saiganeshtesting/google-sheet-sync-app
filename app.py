from fastapi import FastAPI
from sheets_sync.core import sync_sheets

app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.get("/sync")
def run_sync():
    result = sync_sheets()
    return {"status": result}
