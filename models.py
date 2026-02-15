"""
Data models for PDF to JSON extractor.
Defines the JSON schema using Pydantic.
Includes both full schema (for output) and compact schema (for LLM to reduce tokens).
"""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class PageType(str, Enum):
    """Fixed page type categories."""
    COVER = "cover"
    PROBLEM = "problem"
    CURRENT_SOLUTION = "current_solution"
    SOLUTION_OVERVIEW = "solution_overview"
    FEATURES = "features"
    WORKFLOW_USER_JOURNEY = "workflow_user_journey"
    ARCHITECTURE_DIAGRAM = "architecture_diagram"
    HARDWARE_COMPONENTS = "hardware_components"
    IMPACT_METRICS = "impact_metrics"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    BUSINESS_MODEL = "business_model"
    COSTS_PRICING = "costs_pricing"
    MARKET_SIZING = "market_sizing"
    TRACTION = "traction"
    ROADMAP = "roadmap"
    TEAM = "team"
    APPENDIX = "appendix"
    OTHER = "other"


class Language(str, Enum):
    """Supported languages."""
    ARABIC = "ar"
    ENGLISH = "en"
    MIXED = "mixed"


class ExtractedNumber(BaseModel):
    """A number extracted from the page with context."""
    raw: str = Field(..., description="Exact string found (e.g., '60%')")
    value: float = Field(..., description="Numeric value only")
    unit: str = Field(..., description="Unit (e.g., '%', 'SAR', 'ريال')")
    context: str = Field(..., description="What the number refers to")
    evidence: Literal["text_layer", "ocr", "vision"] = Field(..., description="Source of the number")
    note: Optional[str] = Field(None, description="Optional additional note")


class Confidence(BaseModel):
    """Confidence scores for different extraction aspects."""
    facts: float = Field(..., ge=0.0, le=1.0, description="Confidence in extracted facts")
    visuals: float = Field(..., ge=0.0, le=1.0, description="Confidence in visual explanation")
    inference: float = Field(..., ge=0.0, le=1.0, description="Confidence in inferred message")


class Page(BaseModel):
    """Per-page extraction object."""
    page_index: int = Field(..., ge=1, description="Sequential page number (1-indexed)")
    page_type: PageType = Field(..., description="Page category from fixed enum")
    title: str = Field(..., min_length=1, description="Short meaningful title")
    clean_facts: List[str] = Field(default_factory=list, description="Concise, non-redundant facts")
    visual_explanation: List[str] = Field(default_factory=list, description="Explanation of visuals")
    inferred_message: str = Field(default="", description="One-sentence summary of page intent")
    assumptions_and_gaps: List[str] = Field(default_factory=list, description="Missing info or assumptions")
    extracted_numbers: List[ExtractedNumber] = Field(default_factory=list, description="All numbers with context")
    confidence: Confidence = Field(..., description="Confidence scores")

    @field_validator("clean_facts")
    @classmethod
    def no_empty_facts(cls, v: List[str]) -> List[str]:
        """Remove empty strings from facts."""
        return [fact for fact in v if fact.strip()]

    @field_validator("visual_explanation")
    @classmethod
    def no_empty_visuals(cls, v: List[str]) -> List[str]:
        """Remove empty strings from visuals."""
        return [visual for visual in v if visual.strip()]


class Source(BaseModel):
    """Source document metadata."""
    filename: str = Field(..., description="Original filename")
    file_type: Literal["pdf"] = Field("pdf", description="File type (always pdf in v1)")


class DocumentSummary(BaseModel):
    """Document-level summary generated after all pages are processed."""
    one_paragraph: str = Field(default="", description="One-paragraph summary of entire document")
    key_metrics: List[str] = Field(default_factory=list, description="Most important metrics across all pages")
    key_entities: List[str] = Field(default_factory=list, description="Important stakeholders, users, entities")
    top_claims: List[str] = Field(default_factory=list, description="Main claims or value propositions")
    risks_and_gaps: List[str] = Field(default_factory=list, description="Overall risks and missing information")


class Document(BaseModel):
    """Top-level document object."""
    schema_version: Literal["1.0"] = Field("1.0", description="Schema version")
    document_id: str = Field(..., description="Unique document identifier (UUID)")
    source: Source = Field(..., description="Source file metadata")
    language: Language = Field(..., description="Document language")
    page_count: int = Field(..., ge=1, description="Total number of pages")
    pages: List[Page] = Field(default_factory=list, description="Per-page extractions")
    document_summary: DocumentSummary = Field(default_factory=DocumentSummary, description="Document-level summary")

    @field_validator("pages")
    @classmethod
    def validate_page_indices(cls, v: List[Page], info) -> List[Page]:
        """Ensure page indices are sequential starting from 1."""
        if v:
            expected_indices = list(range(1, len(v) + 1))
            actual_indices = [p.page_index for p in v]
            if actual_indices != expected_indices:
                raise ValueError(f"Page indices must be sequential 1..{len(v)}, got {actual_indices}")
        return v

    def model_post_init(self, __context) -> None:
        """Validate page_count matches number of pages."""
        if len(self.pages) != self.page_count:
            raise ValueError(f"page_count ({self.page_count}) must equal len(pages) ({len(self.pages)})")


# ============================================================================
# COMPACT MODELS (for LLM output - reduces tokens by 40%)
# ============================================================================

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
