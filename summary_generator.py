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
        """Build system prompt for summary generation."""
        return """You are a fair, thorough presentation analyst. Analyze comprehensively but efficiently.

RULES:
- Return ONLY valid JSON
- Synthesize ALL important information across pages
- Be thorough but concise (brief phrases, no fluff)
- Give presenters a fair chance - capture all key points
- Identify both strengths and gaps"""
    
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
        
        prompt = f"""Analyze this presentation comprehensively and fairly. Include ALL important information.

EXTRACTED PAGES:
{pages_json}

OUTPUT SCHEMA (JSON):
{{
  "one_paragraph": "4-5 sentence comprehensive overview covering: what this is, who it's for, main value, approach, and outcome",
  "key_metrics": ["metric1: X% improvement", "metric2: Y users", ...],
  "key_entities": ["entity 1", "entity 2", ...],
  "top_claims": ["claim 1", "claim 2", ...],
  "risks_and_gaps": ["gap 1", "gap 2", ...]
}}

COMPREHENSIVE REQUIREMENTS:
1. one_paragraph: 4-5 sentences covering the full story
2. key_metrics: 8-12 most important numbers/metrics with context (be thorough)
3. key_entities: 5-10 stakeholders, users, partners, competitors mentioned
4. top_claims: 6-10 main value propositions, benefits, or differentiators
5. risks_and_gaps: 5-8 concerns, missing info, assumptions, or weaknesses

FAIRNESS: This is someone's presentation. Capture ALL significant points. Don't skip important information.
EFFICIENCY: Use brief phrases. Avoid redundancy. Be precise.

Return JSON only."""
        
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
            
            # o1 models don't support temperature parameter
            if not self.model.startswith("o1"):
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
