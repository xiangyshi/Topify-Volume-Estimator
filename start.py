#!/usr/bin/env python3
"""
Startup script for Render.com deployment
"""
import os
import sys

def main():
    # Ensure we're in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Set environment variables for production
    os.environ.setdefault('FLASK_ENV', 'production')
    
    # Import and run the web server
    try:
        from web_server import app
        
        # Get port from environment
        port = int(os.environ.get('PORT', 5000))
        
        print(f"Starting Topify ChatGPT Volume Estimator on port {port}")
        print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
        
        # Run the app
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
