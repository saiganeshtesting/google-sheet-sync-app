from flask import Flask, request
import threading
import sync_core

app = Flask(__name__)

@app.route('/')
def index():
    return "✅ Google Sheet Sync App is Running!"

@app.route('/sync', methods=['POST'])
def sync():
    def run_sync():
        print("Starting sync process...")
        sync_core.main()
        print("Sync complete.")
    
    threading.Thread(target=run_sync).start()
    return {"status": "Sync started"}, 202

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
