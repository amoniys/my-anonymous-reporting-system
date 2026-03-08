import uvicorn
from backend.app import app

if __name__ == "__main__":
    print("Starting Anonymous Reporting System...")
    print("- Open your browser to http://127.0.0.1:8000")
    print("- The system includes 4 modules: Submission, Verification, Storage, Abuse Control.")
    print("- A WebSocket endpoint at /ws provides live updates.")
    print("- An AI review endpoint is available at /api/v1/ai_review for model integration.")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")