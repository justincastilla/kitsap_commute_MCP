# Kitsap Commute Helper

A full-stack app to help Kitsap County residents decide whether to take the ferry or drive to Seattle events, using real-time WSDOT and Google Maps data.

## Backend
- Python, FastAPI
- MCP server stubs for WSDOT and Google Maps APIs

## Frontend
- React, Axios

## Getting Started
1. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```
2. Install frontend dependencies:
   ```bash
   cd ../frontend
   npm install
   npm start
   ```
3. Connect MCP servers as needed for API access.

---

This is a starter template. Replace MCP stubs with actual calls and add logic as needed.
