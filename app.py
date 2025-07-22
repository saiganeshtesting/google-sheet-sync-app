from flask import Flask, jsonify
from gsheet_sync import run_sync

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Google Sheet Sync App is Running!"

@app.route("/sync")
def sync():
    try:
        run_sync()
        return jsonify({"status": "✅ Success", "details": "Sync completed."})
    except Exception as e:
        import traceback
        return jsonify({
            "status": "❌ Error",
            "details": str(e),
            "trace": traceback.format_exc()
        })
