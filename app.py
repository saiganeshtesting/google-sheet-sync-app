from fastapi import FastAPI
from sheets_sync import sync_data

app = FastAPI()

@app.get("/sync")
def sync_sheets():
    result = sync_data()
    return {"status": result}
