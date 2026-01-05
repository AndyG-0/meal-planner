#!/usr/bin/env python3
"""Simple script to test the backend API."""

import uvicorn

from app.main import app

if __name__ == "__main__":
    print("Starting Meal Planner API server...")
    print("API documentation available at: http://localhost:8180/docs")
    print("Health check at: http://localhost:8180/health")
    uvicorn.run(app, host="0.0.0.0", port=8180)
