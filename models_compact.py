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
    t: str = Field(..., description="Page type - must be one value")
    ti: str = Field(..., min_length=1, description="Title")
    
    @field_validator("t")
    @classmethod
    def validate_page_type(cls, v: str) -> str:
        """Validate and normalize page_type."""
        # Valid page types from the enum
        valid_types = {
            "cover", "problem", "current_solution", "solution_overview",
            "features", "workflow_user_journey", "architecture_diagram",
            "hardware_components", "impact_metrics", "competitive_analysis",
            "business_model", "costs_pricing", "market_sizing", "traction",
            "roadmap", "team", "appendix", "other"
        }
        
        v_clean = v.strip().lower()
        
        # If it contains pipes, take the first valid one
        if "|" in v_clean:
            parts = v_clean.split("|")
            for part in parts:
                if part.strip() in valid_types:
                    return part.strip()
        
        # If it's valid, return it
        if v_clean in valid_types:
            return v_clean
        
        # Try fuzzy matching
        if "cover" in v_clean:
            return "cover"
        elif "problem" in v_clean:
            return "problem"
        elif "solution" in v_clean and "current" in v_clean:
            return "current_solution"
        elif "solution" in v_clean:
            return "solution_overview"
        elif "feature" in v_clean:
            return "features"
        elif "workflow" in v_clean or "journey" in v_clean:
            return "workflow_user_journey"
        elif "architecture" in v_clean or "diagram" in v_clean:
            return "architecture_diagram"
        elif "hardware" in v_clean or "component" in v_clean:
            return "hardware_components"
        elif "impact" in v_clean or "metric" in v_clean:
            return "impact_metrics"
        elif "competitive" in v_clean or "competition" in v_clean:
            return "competitive_analysis"
        elif "business" in v_clean or "model" in v_clean:
            return "business_model"
        elif "cost" in v_clean or "pricing" in v_clean:
            return "costs_pricing"
        elif "market" in v_clean or "sizing" in v_clean:
            return "market_sizing"
        elif "traction" in v_clean:
            return "traction"
        elif "roadmap" in v_clean:
            return "roadmap"
        elif "team" in v_clean:
            return "team"
        elif "appendix" in v_clean:
            return "appendix"
        
        # Default to "other"
        return "other"
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
