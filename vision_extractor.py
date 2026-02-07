"""
Vision-based extraction using LLM (GPT-4 Vision).
Processes page images with text context to extract structured information.
"""
import logging
import json
import base64
from io import BytesIO
from typing import Dict, Any
from PIL import Image
from openai import OpenAI
from models import Page, PageType, Confidence, ExtractedNumber
from models_compact import CompactPage, compact_to_full

logger = logging.getLogger(__name__)


class VisionExtractor:
    """Extracts structured information from PDF pages using vision LLM."""
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "gpt-4o",
        max_image_size: int = 1024,
        image_quality: int = 75,
        detail_level: str = "low",
        max_text_length: int = 500,
        max_facts: int = 5,
        max_visuals: int = 3,
        max_gaps: int = 3
    ):
        """
        Initialize vision extractor.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (must support vision)
            max_image_size: Max width/height for images (reduces tokens)
            image_quality: JPEG quality 1-100 (lower = fewer tokens)
            detail_level: "low" (65 tokens) or "high" (expensive)
            max_text_length: Max chars for text context (truncates)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_image_size = max_image_size
        self.image_quality = image_quality
        self.detail_level = detail_level
        self.max_text_length = max_text_length
        self.max_facts = max_facts
        self.max_visuals = max_visuals
        self.max_gaps = max_gaps
    
    def _resize_image(self, image: Image.Image) -> Image.Image:
        """Resize image to reduce token usage while keeping aspect ratio."""
        width, height = image.size
        
        # If image is already small enough, don't resize
        if width <= self.max_image_size and height <= self.max_image_size:
            return image
        
        # Calculate new size maintaining aspect ratio
        if width > height:
            new_width = self.max_image_size
            new_height = int(height * (self.max_image_size / width))
        else:
            new_height = self.max_image_size
            new_width = int(width * (self.max_image_size / height))
        
        logger.info(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """
        Convert PIL Image to base64 string with optimization.
        Uses JPEG compression to drastically reduce token usage.
        """
        # Resize image first
        image = self._resize_image(image)
        
        # Convert to RGB if needed (JPEG doesn't support transparency)
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        
        # Save as JPEG with compression
        buffered = BytesIO()
        image.save(buffered, format='JPEG', quality=self.image_quality, optimize=True)
        size_kb = len(buffered.getvalue()) / 1024
        logger.info(f"Compressed image to {size_kb:.1f} KB (quality={self.image_quality})")
        
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for extraction (ultra-minimal for token reduction)."""
        return """Extract facts ONLY. JSON format. NO REASONING. NO THINKING. Direct extraction."""
    
    def _build_user_prompt(self, page_index: int, text_layer: str, ocr_text: str) -> str:
        """
        Build the user prompt for a specific page (truncated for token reduction).
        
        Args:
            page_index: Page number (1-indexed)
            text_layer: Text from PDF text layer
            ocr_text: Text from OCR
        
        Returns:
            Formatted prompt string
        """
        # Truncate text to reduce tokens
        text_preview = text_layer[:self.max_text_length] if text_layer else "(none)"
        ocr_preview = ocr_text[:self.max_text_length] if ocr_text else "(none)"
        
        if len(text_layer) > self.max_text_length:
            text_preview += "..."
        if len(ocr_text) > self.max_text_length:
            ocr_preview += "..."
        
        prompt = f"""P{page_index}. {text_preview}

EXTRACT FACTS ONLY. NO REASONING.

Schema:
{{"p":{page_index},"t":"cover|problem|solution_overview|features|workflow_user_journey|architecture_diagram|hardware_components|impact_metrics|business_model|costs_pricing|market_sizing|traction|roadmap|team|other",
"ti":"page title","f":["fact1","fact2"],"v":["visual desc"],"m":"1 sentence summary",
"g":["gap1"],"n":[{{"r":"60%","val":60.0,"u":"%","c":"water reduction","e":"ocr"}}],
"conf":{{"f":0.9,"v":0.9,"i":0.9}}}}

RULES:
- n.val MUST be number (not text!)
- If no numbers visible, n=[]
- Max f={self.max_facts}, v={self.max_visuals}, g={self.max_gaps}
- Brief facts only
- NO REASONING OR THINKING"""
        
        return prompt
    
    def extract_page(
        self,
        page_index: int,
        image: Image.Image,
        text_layer: str = "",
        ocr_text: str = ""
    ) -> Page:
        """
        Extract structured information from a single page.
        
        Args:
            page_index: Page number (1-indexed)
            image: Page image
            text_layer: Text from PDF text layer
            ocr_text: Text from OCR
        
        Returns:
            Page object with extracted information
        """
        logger.info(f"Extracting page {page_index} using vision LLM")
        
        try:
            # Convert image to base64
            image_base64 = self._image_to_base64(image)
            
            # Build prompts
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(page_index, text_layer, ocr_text)
            
            # Build API call parameters
            api_params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": self.detail_level  # "low" = 65 tokens, "high" = expensive
                                }
                            }
                        ]
                    }
                ],
                "response_format": {"type": "json_object"}
            }
            
            # Set temperature based on model
            model_lower = self.model.lower()
            if model_lower.startswith("o1") or model_lower.startswith("gpt-5"):
                # o1/gpt-5 models only support temperature=1
                api_params["temperature"] = 1
            else:
                # Other models support lower temperature for consistency
                api_params["temperature"] = 0.1
            
            # Call OpenAI API with token optimization
            response = self.client.chat.completions.create(**api_params)
            
            # Log token usage
            if hasattr(response, 'usage'):
                logger.info(f"Page {page_index} tokens: {response.usage.total_tokens} "
                          f"(prompt: {response.usage.prompt_tokens}, completion: {response.usage.completion_tokens})")
            
            # Parse response
            response_text = response.choices[0].message.content
            logger.debug(f"LLM response for page {page_index}: {response_text[:200]}...")
            
            # Parse JSON (expecting compact format)
            page_data = json.loads(response_text)
            
            # Normalize evidence fields in compact format (fix common LLM mistakes)
            if "n" in page_data:  # compact numbers field
                for num in page_data["n"]:
                    if "e" in num:
                        evidence_lower = str(num["e"]).lower().strip()
                        # Map common variations to valid values
                        if "text" in evidence_lower and "layer" in evidence_lower:
                            num["e"] = "text_layer"
                        elif "ocr" in evidence_lower:
                            num["e"] = "ocr"
                        elif "vision" in evidence_lower or "visual" in evidence_lower:
                            num["e"] = "vision"
                        else:
                            logger.warning(f"Unknown evidence value '{num['e']}', defaulting to 'vision'")
                            num["e"] = "vision"
            
            # Create CompactPage object (Pydantic will validate)
            compact_page = CompactPage(**page_data)
            
            # Convert to full Page format
            full_page_data = compact_to_full(compact_page)
            page = Page(**full_page_data)
            
            logger.info(f"Successfully extracted page {page_index}: {page.title}")
            return page
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON for page {page_index}: {e}")
            logger.error(f"Response was: {response_text}")
            raise ValueError(f"Invalid JSON response for page {page_index}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to extract page {page_index}: {e}")
            raise RuntimeError(f"Page extraction failed for page {page_index}: {e}")
    
    def extract_page_with_retry(
        self,
        page_index: int,
        image: Image.Image,
        text_layer: str = "",
        ocr_text: str = "",
        retry_instruction: str = ""
    ) -> Page:
        """
        Extract page with optional retry instruction (for quality control).
        
        Args:
            page_index: Page number
            image: Page image
            text_layer: PDF text layer
            ocr_text: OCR text
            retry_instruction: Additional instruction for retry (e.g., "Focus on capturing ALL numbers")
        
        Returns:
            Page object
        """
        if retry_instruction:
            logger.info(f"Retrying page {page_index} with instruction: {retry_instruction}")
            # Append retry instruction to user prompt
            original_prompt = self._build_user_prompt(page_index, text_layer, ocr_text)
            modified_prompt = f"{original_prompt}\n\nIMPORTANT RETRY INSTRUCTION: {retry_instruction}"
            
            # Build custom request
            image_base64 = self._image_to_base64(image)
            system_prompt = self._build_system_prompt()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": modified_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content
            page_data = json.loads(response_text)
            return Page(**page_data)
        else:
            return self.extract_page(page_index, image, text_layer, ocr_text)
