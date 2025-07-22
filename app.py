from fastapi import FastAPI
from fastapi.responses import JSONResponse
from gsheet_sync import run_sync

app = FastAPI()

@app.get("/")
def root():
    return {"status": "✅ Ready"}

@app.get("/sync")
def sync():
    try:
        run_sync()
        return {"status": "✅ Success"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "❌ Error",
                "details": str(e),
                "trace": repr(e),
            }
        )
