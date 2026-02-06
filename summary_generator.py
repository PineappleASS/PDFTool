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
        return """You are a document analysis system. Your task is to create a concise document-level summary based on extracted page information.

CRITICAL RULES:
- Return ONLY valid JSON matching the exact schema
- No markdown, no code blocks, no extra text
- Synthesize information across all pages
- Be concise and focus on the most important information
- Extract key metrics, entities, claims, and identify gaps"""
    
    def _build_user_prompt(self, pages: List[Page]) -> str:
        """
        Build user prompt with page summaries.
        
        Args:
            pages: List of extracted pages
        
        Returns:
            Formatted prompt
        """
        # Create a condensed view of all pages
        page_summaries = []
        for page in pages:
            summary = {
                "page": page.page_index,
                "type": page.page_type,
                "title": page.title,
                "facts": page.clean_facts[:5],  # Top 5 facts
                "message": page.inferred_message,
                "numbers": [
                    f"{num.raw} ({num.context})"
                    for num in page.extracted_numbers[:3]  # Top 3 numbers
                ]
            }
            page_summaries.append(summary)
        
        pages_json = json.dumps(page_summaries, ensure_ascii=False, indent=2)
        
        prompt = f"""Create a document-level summary based on these extracted pages.

EXTRACTED PAGES:
{pages_json}

OUTPUT SCHEMA (JSON only):
{{
  "one_paragraph": "concise paragraph summarizing the entire document (2-3 sentences)",
  "key_metrics": ["most important metric 1", "most important metric 2", ...],
  "key_entities": ["stakeholder 1", "user group 1", "company 1", ...],
  "top_claims": ["main value proposition", "key claim 2", ...],
  "risks_and_gaps": ["overall risk 1", "missing information 1", ...]
}}

REQUIREMENTS:
1. one_paragraph: 2-3 sentence summary of what this document is about
2. key_metrics: 3-5 most important numbers/metrics across all pages
3. key_entities: 3-7 important stakeholders, users, companies, or entities
4. top_claims: 3-5 main claims or value propositions
5. risks_and_gaps: 3-5 overall risks or missing information

Be concise. Focus on what matters most.

Return ONLY the JSON object."""
        
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
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
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
