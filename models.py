"""
Data models for PDF to JSON extractor.
Defines the JSON schema using Pydantic.
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
