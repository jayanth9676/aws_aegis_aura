"""Script to run both backend and frontend locally."""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

def run_backend():
    """Start the FastAPI backend server."""
    print("Starting backend server on http://localhost:8000...")
    backend_cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.api.app:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    return subprocess.Popen(backend_cmd, cwd=Path(__file__).parent)

def run_frontend():
    """Start the Next.js frontend server."""
    print("Starting frontend server on http://localhost:3000...")
    frontend_dir = Path(__file__).parent / "frontend"
    frontend_cmd = ["npm", "run", "dev"]
    return subprocess.Popen(frontend_cmd, cwd=frontend_dir, shell=True)

def main():
    """Main function to run both servers."""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     AEGIS - Local Development Environment                   ║
    ║                                                              ║
    ║     Starting Backend (FastAPI) and Frontend (Next.js)       ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    backend_process = None
    frontend_process = None
    
    try:
        # Start backend
        backend_process = run_backend()
        time.sleep(3)  # Give backend time to start
        
        # Start frontend
        frontend_process = run_frontend()
        time.sleep(2)
        
        print("\n" + "="*70)
        print("✓ Backend running at:  http://localhost:8000")
        print("✓ Frontend running at: http://localhost:3000")
        print("✓ API docs at:         http://localhost:8000/docs")
        print("="*70)
        print("\nPress Ctrl+C to stop both servers...")
        
        # Wait for processes
        backend_process.wait()
        
    except KeyboardInterrupt:
        print("\n\nShutting down servers...")
        
    finally:
        # Cleanup
        if backend_process:
            backend_process.terminate()
            backend_process.wait()
        if frontend_process:
            frontend_process.terminate()
            frontend_process.wait()
        
        print("Servers stopped.")

if __name__ == "__main__":
    main()

