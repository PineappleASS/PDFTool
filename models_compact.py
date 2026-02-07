"""
Compact data models for reduced output tokens.
Uses abbreviated field names to minimize LLM output token usage.
"""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from models import PageType, Language


class CompactExtractedNumber(BaseModel):
    """Compact number extraction (shorter field names)."""
    r: str = Field(..., description="Raw string")
    val: float = Field(..., description="Numeric value")
    u: str = Field(..., description="Unit")
    c: str = Field(..., description="Context")
    e: Literal["text_layer", "ocr", "vision"] = Field(..., description="Evidence")
    note: Optional[str] = Field(None, description="Optional note")


class CompactConfidence(BaseModel):
    """Compact confidence scores."""
    f: float = Field(..., ge=0.0, le=1.0, description="Facts confidence")
    v: float = Field(..., ge=0.0, le=1.0, description="Visuals confidence")
    i: float = Field(..., ge=0.0, le=1.0, description="Inference confidence")


class CompactPage(BaseModel):
    """Compact per-page extraction (reduces output tokens by ~40%)."""
    p: int = Field(..., ge=1, description="Page index")
    t: str = Field(..., description="Page type")
    ti: str = Field(..., min_length=1, description="Title")
    f: List[str] = Field(default_factory=list, description="Facts")
    v: List[str] = Field(default_factory=list, description="Visuals")
    m: str = Field(default="", description="Message")
    g: List[str] = Field(default_factory=list, description="Gaps")
    n: List[CompactExtractedNumber] = Field(default_factory=list, description="Numbers")
    conf: CompactConfidence = Field(..., description="Confidence")

    @field_validator("f")
    @classmethod
    def no_empty_facts(cls, v: List[str]) -> List[str]:
        return [fact for fact in v if fact.strip()]

    @field_validator("v")
    @classmethod
    def no_empty_visuals(cls, v: List[str]) -> List[str]:
        return [visual for visual in v if visual.strip()]


def compact_to_full(compact: CompactPage) -> dict:
    """Convert compact page to full schema for human readability."""
    from models import ExtractedNumber, Confidence
    
    return {
        "page_index": compact.p,
        "page_type": compact.t,
        "title": compact.ti,
        "clean_facts": compact.f,
        "visual_explanation": compact.v,
        "inferred_message": compact.m,
        "assumptions_and_gaps": compact.g,
        "extracted_numbers": [
            {
                "raw": n.r,
                "value": n.val,
                "unit": n.u,
                "context": n.c,
                "evidence": n.e,
                "note": n.note
            }
            for n in compact.n
        ],
        "confidence": {
            "facts": compact.conf.f,
            "visuals": compact.conf.v,
            "inference": compact.conf.i
        }
    }
