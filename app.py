from flask import Flask, jsonify 
from gsheet_sync import run_sync
import traceback

app = Flask(__name__)

@app.route("/")
def home():
    return "✨ GSheet Sync API is running. Use /sync to trigger sync."

@app.route("/sync", methods=["GET"])
def sync():
    try:
        run_sync()
        return jsonify({"status": "✅ Synced successfully"})
    except Exception as e:
        return jsonify({
            "status": "❌ Error",
            "details": str(e),
            "trace": traceback.format_exc()
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
