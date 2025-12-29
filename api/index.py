# Vercel entrypoint for AI ATS Resume Checker
import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app
from app import app

# Expose the app for Vercel - both 'app' and 'application' for compatibility
application = app

# Handler function for Vercel serverless
def handler(request, response):
    return app(request, response)
