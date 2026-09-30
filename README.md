# ⚖️ LegalEase — AI-Powered Legal Document Generator

Generates draft legal documents (contracts, NDAs, lease agreements, and more) from a
few plain-English inputs, using Google Gemini. Built with **FastAPI** (backend) and
**Streamlit** (frontend), with export to **.txt**, **.docx**, and **.pdf**.

> ⚠️ **Not legal advice.** LegalEase drafts a starting point only. Always have a
> qualified attorney review any document before you sign or send it.

## Folder structure
```
LegalEase/
├── legalEaseAPI/
│   ├── main.py          # FastAPI app (routes, CORS, health check)
│   └── routes.py        # POST /generate endpoint + request validation
├── ai_core/
│   └── gemini_generator.py   # Gemini calls with automatic model fallback
├── frontend/
│   └── app.py            # Streamlit UI: inputs, preview, edit, download
├── Image/
│   ├── Logo.png           # used in the Streamlit header + .docx/.pdf exports
│   └── inverseLogo.png
├── utils.py               # sanitize_text, format_docx, format_pdf, format_html_preview
├── config.py               # loads .env, shared by backend + frontend
├── requirements.txt
├── .env.example
└── .gitignore
```

## Setup (5 minutes)

1. **Python 3.10+** — check with `python --version`.
2. **Create a virtual environment and install packages**
   ```bash
   python -m venv venv
   # Windows:   venv\Scripts\activate
   # Mac/Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Get a free Gemini API key:** https://aistudio.google.com/apikey
4. **Create your `.env` file:** copy `.env.example` to `.env` and paste your key:
   ```
   GEMINI_API_KEY=AIza...your key...
   ```
5. **Start the backend** (terminal 1):
   ```bash
   uvicorn legalEaseAPI.main:app --reload
   ```
   Runs at http://127.0.0.1:8000 — check http://127.0.0.1:8000/health.
6. **Start the frontend** (terminal 2, same folder):
   ```bash
   streamlit run frontend/app.py
   ```
   Opens at http://localhost:8501.

## How it works

1. You fill in **Document Type**, **Parties Involved**, **Terms & Conditions**
   (semicolon-separated), and **Effective Date** in the Streamlit UI.
2. Streamlit sends a `POST /generate` request to the FastAPI backend.
3. The backend calls `GeminiDocumentGenerator`, which builds a legal-drafting
   prompt and calls Gemini — automatically retrying the next supported model
   if the configured one is rate-limited, retired, or briefly unavailable.
4. The generated text comes back to Streamlit, where you can preview it,
   edit it inline, and download it as `.txt`, `.docx` (with your logo and a
   terms table), or `.pdf` (with a logo header and page-numbered footer).

## Why the model fallback matters

The original project spec called for **gemini-1.5-pro**. That model (and the
1.5 line generally) has since been **retired** by Google, so a hard-coded
call to it fails with a `404 NOT_FOUND` error on every request — exactly the
failure the EduGenie project hit in production. `ai_core/gemini_generator.py`
avoids that by keeping an ordered list of currently supported models
(`GEMINI_MODEL` + `GEMINI_FALLBACK_MODELS` in `.env`) and retrying the next
one automatically on a 404 / 429 / 5xx error, so the app keeps working as
Google updates its model lineup.

## Troubleshooting

- **"Can't reach the LegalEase backend"** → start `uvicorn legalEaseAPI.main:app --reload` first, and run Streamlit from the same project folder.
- **"GEMINI_API_KEY is not set"** → `.env` missing or not filled in; restart the backend after editing it.
- **"Gemini rejected the API key"** → the key was copied incorrectly; generate a new one in AI Studio.
- **Logo missing in exports** → replace `Image/Logo.png` with your own logo; exports still work fine without it.
- **Port already in use** → `uvicorn legalEaseAPI.main:app --reload --port 8001` and update `BACKEND_URL` in `.env` to match.

## Example inputs (from the original demo script)

- **NDA:** parties = "Jane Doe (Service Provider), TechNova Inc. (Client)"; terms = "Confidentiality must be maintained at all times; Either party may terminate with 15 days notice"; date = "April 15, 2025".
- **Lease Agreement:** document type = "Residential Lease Agreement"; include the property address and tenant details in "Parties Involved".
