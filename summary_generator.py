"""
Document-level summary generation.
"""
import logging
import json
from typing import List
from openai import OpenAI
from models import Page, DocumentSummary

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """Generates document-level summaries from extracted pages."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initialize summary generator.
        
        Args:
            api_key: OpenAI API key
            model: Model to use
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for summary generation (ultra-minimal)."""
        return """Summarize presentation. JSON only. Brief. NO REASONING. Direct synthesis."""
    
    def _build_user_prompt(self, pages: List[Page]) -> str:
        """
        Build user prompt with comprehensive page summaries for fair analysis.
        
        Args:
            pages: List of extracted pages
        
        Returns:
            Formatted prompt
        """
        # Create comprehensive view of all pages (include ALL info for fairness)
        page_summaries = []
        for page in pages:
            summary = {
                "page": page.page_index,
                "type": page.page_type,
                "title": page.title,
                "facts": page.clean_facts,  # ALL facts (not limited)
                "visuals": page.visual_explanation,  # Include visuals
                "message": page.inferred_message,
                "gaps": page.assumptions_and_gaps,  # Include gaps
                "numbers": [
                    f"{num.raw} ({num.context})"
                    for num in page.extracted_numbers  # ALL numbers
                ]
            }
            page_summaries.append(summary)
        
        pages_json = json.dumps(page_summaries, ensure_ascii=False, indent=2)
        
        prompt = f"""Pages:{pages_json}

Schema:
{{"one_paragraph":"4-5 sentences","key_metrics":["8-12"],"key_entities":["5-10"],"top_claims":["6-10"],"risks_and_gaps":["5-8"]}}

NO REASONING. Direct synthesis. Brief. JSON."""
        
        return prompt
    
    def generate_summary(self, pages: List[Page]) -> DocumentSummary:
        """
        Generate document summary from extracted pages.
        
        Args:
            pages: List of extracted pages
        
        Returns:
            DocumentSummary object
        """
        logger.info(f"Generating document summary from {len(pages)} pages")
        
        if not pages:
            logger.warning("No pages provided, returning empty summary")
            return DocumentSummary()
        
        try:
            # Build prompts
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(pages)
            
            # Build API call parameters
            api_params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
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
                api_params["temperature"] = 0.2
            
            # Call OpenAI API
            response = self.client.chat.completions.create(**api_params)
            
            # Log token usage for summary
            if hasattr(response, 'usage'):
                logger.info(f"Summary generation tokens: {response.usage.total_tokens} "
                          f"(prompt: {response.usage.prompt_tokens}, completion: {response.usage.completion_tokens})")
            
            # Parse response
            response_text = response.choices[0].message.content
            logger.debug(f"Summary response: {response_text[:200]}...")
            
            # Parse JSON
            summary_data = json.loads(response_text)
            
            # Create DocumentSummary object
            summary = DocumentSummary(**summary_data)
            
            logger.info("Successfully generated document summary")
            return summary
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON for summary: {e}")
            logger.error(f"Response was: {response_text}")
            return DocumentSummary()
        
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return DocumentSummary()
