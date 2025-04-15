import sys

# --- Entry Point for the Application ---
if __name__ == "__main__":
    # Determine which app to run based on command-line argument
    # Default to "flask" if no argument is provided
    mode = sys.argv[1] if len(sys.argv) > 1 else "flask"

    if mode == "flask":
        # Run the Flask dashboard frontend
        from app.flask_app import app
        app.run(debug=True)

    elif mode == "fastapi":
        # Run the FastAPI backend for categorization
        import uvicorn
        uvicorn.run("app.fastapi_app:app", host="127.0.0.1", port=8010, reload=True)
