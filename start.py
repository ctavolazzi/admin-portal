#!/usr/bin/env python3
"""
Simple startup script for the Admin Portal
Uses Poetry for dependency management
"""

import os
import sys
from pathlib import Path

def main():
    """Start the admin portal application"""
    print("🚀 Starting Admin Portal...")

    # Check if we're in Poetry environment
    if not os.environ.get('VIRTUAL_ENV'):
        print("❌ Not in Poetry virtual environment!")
        print("Run: poetry shell")
        print("Or:  poetry run python start.py")
        sys.exit(1)

    # Import and start the Flask app
    try:
        from app import start_server
        print("✅ Dependencies loaded successfully")
        print("🌐 Starting server at http://localhost:8080")
        print("📱 Admin login: admin1 / 1234")
        start_server()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Run: poetry install")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    main()