"""LegalEase - Streamlit frontend.

Run the backend first:  uvicorn legalEaseAPI.main:app --reload
Then, in a second terminal:  streamlit run frontend/app.py
"""
import sys
from pathlib import Path

import requests
import streamlit as st

# Make the project root importable (config.py, utils.py live one level up).
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from config import BACKEND_URL, LOGO_PATH  # noqa: E402
from utils import format_docx, format_html_preview, format_pdf, sanitize_text  # noqa: E402

st.set_page_config(page_title="LegalEase", page_icon="⚖️", layout="centered")

st.markdown(
    """
    <style>
    .stApp { background-color: #0b0f1a; }
    h1, h2, h3, p, label, .stMarkdown, .stCaption { color: #e5e7eb !important; }
    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
        background-color: #151b2b; color: #e5e7eb; border: 1px solid #2b3444;
    }
    div.stButton > button, div.stDownloadButton > button {
        background-color: #7a1f1f; color: #ffffff; border: 1px solid #a33; border-radius: 6px;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover { background-color: #9c2b2b; }
    </style>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image(LOGO_PATH, use_container_width=True)
    except Exception:
        st.markdown("<h1 style='text-align:center;'>⚖️ LegalEase</h1>", unsafe_allow_html=True)

st.markdown("<h3 style='text-align:center;'>AI Legal Document Generator</h3>", unsafe_allow_html=True)
st.caption(
    "⚠️ Drafts generated here are a starting point only — have a qualified attorney "
    "review any document before you sign or send it."
)

document_type = st.text_input("Document Type (Ex: Agreement, Contract, NDA)")
parties = st.text_area("Parties Involved")
terms = st.text_area("Terms & Conditions (Use semicolons for bullet points)")
dates = st.text_input("Effective Date")

if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""
if "show_edit" not in st.session_state:
    st.session_state.show_edit = False

if st.button("Generate Document", type="primary"):
    if not all(v.strip() for v in (document_type, parties, terms, dates)):
        st.warning("Please fill in every field before generating a document.")
    else:
        with st.spinner("Drafting your document with Gemini..."):
            resp = None
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/generate",
                    json={"document_type": document_type, "parties": parties, "terms": terms, "dates": dates},
                    timeout=60,
                )
                resp.raise_for_status()
                st.session_state.generated_text = sanitize_text(resp.json()["document"])
                st.session_state.show_edit = False
                st.success("✅ Document Generated Successfully!")
            except requests.exceptions.ConnectionError:
                st.error(
                    "Can't reach the LegalEase backend. Start it first with:\n\n"
                    "`uvicorn legalEaseAPI.main:app --reload`"
                )
            except requests.exceptions.Timeout:
                st.error("The backend took too long to respond. Please try again.")
            except requests.exceptions.HTTPError:
                detail = "Unknown error"
                if resp is not None:
                    try:
                        detail = resp.json().get("detail", detail)
                    except Exception:
                        pass
                st.error(f"Backend error: {detail}")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Something went wrong: {exc}")

if st.session_state.generated_text:
    st.markdown(format_html_preview(st.session_state.generated_text), unsafe_allow_html=True)

    if st.button("✏️ Click to Edit Document"):
        st.session_state.show_edit = not st.session_state.show_edit

    if st.session_state.show_edit:
        st.session_state.generated_text = st.text_area(
            "Edit Document Below:", st.session_state.generated_text, height=300
        )

    file_stub = (document_type or "legal_document").strip().replace(" ", "_").lower() or "legal_document"
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "📄 Download as .TXT", data=st.session_state.generated_text,
            file_name=f"{file_stub}.txt", mime="text/plain",
        )
    with c2:
        st.download_button(
            "🗎 Download as .DOCX",
            data=format_docx(st.session_state.generated_text, document_type, terms),
            file_name=f"{file_stub}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    with c3:
        st.download_button(
            "📕 Download as .PDF",
            data=format_pdf(st.session_state.generated_text, document_type),
            file_name=f"{file_stub}.pdf", mime="application/pdf",
        )
else:
    st.info("Click **Generate Document** to start.")
