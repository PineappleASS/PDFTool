"""
PDF to JSON Extractor

A tool that extracts structured information from PDF presentations
and outputs clean JSON with facts, visual meanings, metrics, and inferred insights.
"""

__version__ = "1.0.0"
__author__ = "PDF Extractor"
__license__ = "MIT"

from .models import Document, Page, PageType, Language
from .pipeline import ExtractionPipeline
from .config import Config

__all__ = [
    'Document',
    'Page',
    'PageType',
    'Language',
    'ExtractionPipeline',
    'Config',
]
