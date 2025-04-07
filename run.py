import sys

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "flask"
    if mode == "flask":
        from app.flask_app import app
        app.run(debug=True)
    elif mode == "fastapi":
        import uvicorn
        uvicorn.run("app.fastapi_app:app", host="127.0.0.1", port=8010, reload=True)
