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

logger = logging.getLogger(__name__)


class VisionExtractor:
    """Extracts structured information from PDF pages using vision LLM."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initialize vision extractor.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (must support vision)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def _image_to_base64(self, image: Image.Image, format: str = "PNG") -> str:
        """Convert PIL Image to base64 string."""
        buffered = BytesIO()
        image.save(buffered, format=format)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for extraction."""
        return """You are a precise information extraction system. Your task is to analyze PDF presentation pages and extract structured information.

CRITICAL RULES:
- Return ONLY valid JSON matching the exact schema provided
- No markdown formatting, no code blocks, no extra text
- Follow the schema exactly - no additional keys
- Extract ALL numbers visible on the page with full context
- For "evidence" field: use ONLY these exact values: "text_layer", "ocr", or "vision" (lowercase, no variations)
- Ignore branding, logos, and decorative elements unless meaningful
- Be concise and avoid redundancy
- Classify page_type accurately from the provided enum"""
    
    def _build_user_prompt(self, page_index: int, text_layer: str, ocr_text: str) -> str:
        """
        Build the user prompt for a specific page.
        
        Args:
            page_index: Page number (1-indexed)
            text_layer: Text from PDF text layer
            ocr_text: Text from OCR
        
        Returns:
            Formatted prompt string
        """
        prompt = f"""Extract structured information from this PDF page (page {page_index}).

INPUTS PROVIDED:
1. Page image (attached)
2. PDF text layer: {text_layer[:500] if text_layer else "(empty)"}
3. OCR text: {ocr_text[:500] if ocr_text else "(empty)"}

OUTPUT SCHEMA (JSON only):
{{
  "page_index": {page_index},
  "page_type": "one of: cover, problem, current_solution, solution_overview, features, workflow_user_journey, architecture_diagram, hardware_components, impact_metrics, competitive_analysis, business_model, costs_pricing, market_sizing, traction, roadmap, team, appendix, other",
  "title": "short meaningful title (required)",
  "clean_facts": ["concise fact 1", "concise fact 2"],
  "visual_explanation": ["what charts show", "what diagrams depict"],
  "inferred_message": "one sentence: what this page communicates",
  "assumptions_and_gaps": ["missing baseline", "no timeframe"],
  "extracted_numbers": [
    {{
      "raw": "60%",
      "value": 60.0,
      "unit": "%",
      "context": "explanation in Arabic or English",
      "evidence": "MUST be exactly one of: text_layer, ocr, vision (lowercase, no other values allowed)",
      "note": "optional or null"
    }}
  ],
  "confidence": {{
    "facts": 0.9,
    "visuals": 0.85,
    "inference": 0.8
  }}
}}

EXTRACTION TASKS:
1. Classify page_type from the enum
2. Create a meaningful title (infer if not explicit)
3. Extract concise clean_facts (not raw OCR dumps)
4. Explain visuals (charts, diagrams, UI screenshots)
5. Write one-sentence inferred_message
6. List assumptions_and_gaps
7. Extract ALL numbers with full context and evidence source
   - For each number, set "evidence" to EXACTLY one of: "text_layer", "ocr", or "vision" (lowercase only)
8. Provide confidence scores (0-1)

IGNORE:
- Repeated logos/branding (unless the brand name is key information)
- Decorative elements
- Tiny UI labels that don't add meaning

Return ONLY the JSON object, no markdown, no extra text."""
        
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
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
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
            
            # Parse response
            response_text = response.choices[0].message.content
            logger.debug(f"LLM response for page {page_index}: {response_text[:200]}...")
            
            # Parse JSON
            page_data = json.loads(response_text)
            
            # Create Page object (Pydantic will validate)
            page = Page(**page_data)
            
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
