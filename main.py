import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # Enable reload in local development by default (when not on Render/production)
    is_dev = os.environ.get("RENDER") is None
    if is_dev:
        uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=True)
    else:
        from api_server import app
        uvicorn.run(app, host="0.0.0.0", port=port)
