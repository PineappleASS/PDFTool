"""
PDF processing: rendering to images and text extraction.
"""
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image
import PyPDF2
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handles PDF rendering and text extraction."""
    
    def __init__(self, scale: float = 2.5):
        """
        Initialize PDF processor.
        
        Args:
            scale: Render scale factor (higher = better quality, slower)
        """
        self.scale = scale
        self.dpi = int(72 * scale)  # 72 DPI is PDF default
    
    def render_pages(self, pdf_path: Path, max_pages: Optional[int] = None) -> List[Image.Image]:
        """
        Render PDF pages to high-resolution images.
        
        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to render (None = all)
        
        Returns:
            List of PIL Images, one per page
        """
        logger.info(f"Rendering PDF: {pdf_path} at {self.dpi} DPI")
        
        try:
            # Determine number of pages to process
            last_page = None
            if max_pages is not None:
                last_page = max_pages
            
            # Convert PDF to images
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                first_page=1,
                last_page=last_page,
                fmt='png'
            )
            
            logger.info(f"Successfully rendered {len(images)} pages")
            return images
            
        except Exception as e:
            logger.error(f"Failed to render PDF: {e}")
            raise RuntimeError(f"PDF rendering failed: {e}")
    
    def extract_text_layer(self, pdf_path: Path) -> List[str]:
        """
        Extract text from PDF's text layer (if available).
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            List of text strings, one per page
        """
        logger.info(f"Extracting text layer from: {pdf_path}")
        
        page_texts = []
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(reader.pages, start=1):
                    try:
                        text = page.extract_text() or ""
                        page_texts.append(text.strip())
                        logger.debug(f"Page {page_num}: extracted {len(text)} chars")
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num}: {e}")
                        page_texts.append("")
            
            logger.info(f"Extracted text from {len(page_texts)} pages")
            return page_texts
            
        except Exception as e:
            logger.error(f"Failed to extract text layer: {e}")
            raise RuntimeError(f"Text extraction failed: {e}")
    
    def get_page_count(self, pdf_path: Path) -> int:
        """
        Get the number of pages in a PDF.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Number of pages
        """
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                return len(reader.pages)
        except Exception as e:
            logger.error(f"Failed to get page count: {e}")
            raise RuntimeError(f"Could not read PDF: {e}")
    
    def process_pdf(self, pdf_path: Path, max_pages: Optional[int] = None) -> Tuple[List[Image.Image], List[str], int]:
        """
        Full PDF processing: render images and extract text.
        
        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to process
        
        Returns:
            Tuple of (images, text_layers, total_page_count)
        """
        # Get total page count
        total_pages = self.get_page_count(pdf_path)
        
        # Limit pages if needed
        pages_to_process = min(total_pages, max_pages) if max_pages else total_pages
        
        logger.info(f"Processing PDF: {total_pages} total pages, processing {pages_to_process}")
        
        # Render pages
        images = self.render_pages(pdf_path, pages_to_process)
        
        # Extract text layer
        text_layers = self.extract_text_layer(pdf_path)[:pages_to_process]
        
        return images, text_layers, pages_to_process
