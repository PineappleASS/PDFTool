"""
Configuration management for the PDF extractor.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""
    
    # OpenAI API
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # PDF Processing
    PDF_RENDER_SCALE = float(os.getenv("PDF_RENDER_SCALE", "2.5"))
    MAX_PAGES_PER_RUN = int(os.getenv("MAX_PAGES_PER_RUN", "20"))
    
    # OCR
    TESSERACT_LANGUAGES = os.getenv("TESSERACT_LANGUAGES", "ara+eng")
    TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")  # Custom tesseract path (Windows)
    
    # PDF Rendering (Windows)
    POPPLER_PATH = os.getenv("POPPLER_PATH", "")  # Custom poppler path (Windows)
    
    # Quality Control
    RETRY_FLAGGED_PAGES = os.getenv("RETRY_FLAGGED_PAGES", "true").lower() == "true"
    RETRY_SCALE_MULTIPLIER = float(os.getenv("RETRY_SCALE_MULTIPLIER", "1.5"))
    
    # Validation
    MIN_TITLE_LENGTH = int(os.getenv("MIN_TITLE_LENGTH", "3"))
    MAX_BRAND_REPETITION = int(os.getenv("MAX_BRAND_REPETITION", "5"))
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set in environment or .env file")
        
        if cls.PDF_RENDER_SCALE < 1.0 or cls.PDF_RENDER_SCALE > 5.0:
            raise ValueError("PDF_RENDER_SCALE must be between 1.0 and 5.0")
