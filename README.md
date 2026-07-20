# SQL Dump Viewbench

SQL Dump Viewbench is a lightweight web application that allows you to parse, browse, and visualize SQL dump files without needing a running database server.

## Features

- **Zero-DB SQL Parser**: Instantly extracts tables, columns, constraints, and rows from SQL dumps on-the-fly.
- **Interactive File Explorer**: Easily upload and delete .sql dump files.
- **Entity-Relationship Diagrams (ERDs)**: Generates visual interactive database schemas using Mermaid.js.
- **Spreadsheet-style Data Grid**: View actual data rows with backend-driven pagination.
- **Sleek Dark UI**: Built with a responsive dark-themed visual design.

## How to Run Locally

1. **Install Dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Start the Server**:
   ```bash
   cd backend && uvicorn app:app --reload --port 8000
   ```

3. **Open Browser**:
   Go to **http://localhost:8000** to upload or select a SQL file.
