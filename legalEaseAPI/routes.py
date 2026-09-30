from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from ai_core.gemini_generator import GeminiDocumentGenerator, GenerationError

router = APIRouter()
gemini_generator = GeminiDocumentGenerator()


class DocumentRequest(BaseModel):
    document_type: str = Field(min_length=2, max_length=200)
    parties: str = Field(min_length=2, max_length=2000)
    terms: str = Field(min_length=2, max_length=5000)
    dates: str = Field(min_length=2, max_length=100)

    @field_validator("*", mode="before")
    @classmethod
    def _strip(cls, value):
        return value.strip() if isinstance(value, str) else value


@router.post("/generate")
def generate_legal_document(request: DocumentRequest):
    try:
        document = gemini_generator.generate_document(
            request.document_type, request.parties, request.terms, request.dates
        )
        return {"document": document}
    except GenerationError as exc:
        status = 503 if "GEMINI_API_KEY" in str(exc) or "API key" in str(exc) else 502
        raise HTTPException(status_code=status, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Document generation failed: {exc}"[:500])
