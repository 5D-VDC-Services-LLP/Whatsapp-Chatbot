# src/main.py
import uvicorn
from fastapi import FastAPI
from src.api.webhook_router import webhook_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Autodesk WhatsApp Integration",
        description="FastAPI backend for WhatsApp + Autodesk chatbot",
        version="1.0.0",
    )

    # Register webhook route
    app.include_router(webhook_router, prefix="/webhook")

    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
