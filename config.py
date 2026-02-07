"""
Configuration management for the PDF extractor.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in the same directory as this script
_config_dir = Path(__file__).parent
_env_path = _config_dir / ".env"

# Try to load from project directory first, then fallback to cwd
if _env_path.exists():
    load_dotenv(_env_path)
    print(f"[Config] Loaded .env from: {_env_path}")
else:
    load_dotenv()  # Fallback to default search
    print(f"[Config] Searching for .env in current directory")


class Config:
    """Application configuration."""
    
    # OpenAI API
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # PDF Processing
    PDF_RENDER_SCALE = float(os.getenv("PDF_RENDER_SCALE", "1.5"))  # Reduced from 2.5 to 1.5
    MAX_PAGES_PER_RUN = int(os.getenv("MAX_PAGES_PER_RUN", "20"))
    
    # Vision Processing (Token Optimization)
    VISION_IMAGE_MAX_SIZE = int(os.getenv("VISION_IMAGE_MAX_SIZE", "1024"))  # Max width/height in pixels
    VISION_IMAGE_QUALITY = int(os.getenv("VISION_IMAGE_QUALITY", "75"))  # JPEG quality 1-100
    VISION_DETAIL_LEVEL = os.getenv("VISION_DETAIL_LEVEL", "low")  # "low" or "high" - low uses 65 tokens max
    MAX_TEXT_CONTEXT_LENGTH = int(os.getenv("MAX_TEXT_CONTEXT_LENGTH", "500"))  # Truncate text sent to LLM
    
    # Output Optimization (per-page limits for token efficiency)
    MAX_FACTS_PER_PAGE = int(os.getenv("MAX_FACTS_PER_PAGE", "5"))  # Limit facts to reduce output tokens
    MAX_VISUALS_PER_PAGE = int(os.getenv("MAX_VISUALS_PER_PAGE", "3"))  # Limit visual explanations
    MAX_GAPS_PER_PAGE = int(os.getenv("MAX_GAPS_PER_PAGE", "3"))  # Limit gaps/assumptions
    
    # Document Summary (comprehensive for fair analysis)
    # Note: Summary is generated once per document, so we can be more generous here
    SUMMARY_DETAIL_LEVEL = os.getenv("SUMMARY_DETAIL_LEVEL", "comprehensive")  # "brief", "balanced", "comprehensive"
    
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
