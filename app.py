from flask import Flask
import subprocess

app = Flask(__name__)

@app.route("/sync", methods=["GET"])
def run_sync():
    subprocess.call(["python", "run_sheets.py"])
    return "✅ Sync Complete"

if __name__ == "__main__":
    app.run(debug=True, port=5000)