import uvicorn
import os
import sys
import webbrowser

# Add backend directory to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")
    
    print("\n" + "="*60)
    print("      VERSIONRAG ENTERPRISE PLATFORM LAUNCHER")
    print("="*60)
    print(f"[*] Access Web App & API at: http://localhost:{port}")
    print(f"[*] Swagger OpenAPI Docs at: http://localhost:{port}/docs")
    print("="*60 + "\n")
    
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
