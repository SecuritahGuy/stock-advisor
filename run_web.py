#!/usr/bin/env python
"""
Run script for the Stock Advisor web application.
"""
import argparse
import logging
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import app
from app.web.app import app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Stock Advisor web application")
    parser.add_argument("--host", default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the server on")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO if not args.debug else logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the app
    app.run(host=args.host, port=args.port, debug=args.debug)
