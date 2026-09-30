from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import GEMINI_API_KEY
from legalEaseAPI.routes import router

app = FastAPI(
    title="LegalEase - AI Legal Document Generator",
    description="Generates draft legal documents with Google Gemini.",
    version="1.0.0",
)

# The Streamlit frontend runs on a different port (8501) during local
# development, so the backend needs to accept cross-origin requests from it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def home():
    return {"message": "Welcome to LegalEase AI Legal Document Generator API"}


@app.get("/health")
def health():
    return {"status": "healthy" if GEMINI_API_KEY else "configuration_required", "gemini_configured": bool(GEMINI_API_KEY)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
