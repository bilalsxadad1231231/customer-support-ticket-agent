# services/llm_service.py
import json
import logging
from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from config.settings import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL,
            temperature=0.1,
            max_tokens=2048
        )
    
    async def classify_ticket(self, subject: str, description: str) -> Dict[str, Any]:
        """Classify support ticket into categories"""
        from prompts.classification import CLASSIFICATION_PROMPT
        
        try:
            prompt = CLASSIFICATION_PROMPT.format(
                subject=subject,
                description=description
            )
            
            messages = [HumanMessage(content=prompt)]
            response = await self.llm.ainvoke(messages)
            
            # Parse JSON response
            result = json.loads(response.content.strip())
            return result
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            # Fallback classification
            return {
                "category": "general",
                "confidence": 0.5,
                "reasoning": "Error in classification, defaulted to general"
            }
    
    async def generate_draft(
        self, 
        subject: str, 
        description: str, 
        category: str, 
        context: str,
        is_redraft: bool = False,
        previous_draft: str = "",
        reviewer_feedback: str = ""
    ) -> str:
        """Generate response draft"""
        from prompts.draft_generation import DRAFT_GENERATION_PROMPT, REDRAFT_PROMPT
        
        try:
            if is_redraft:
                prompt = REDRAFT_PROMPT.format(
                    subject=subject,
                    description=description,
                    category=category,
                    previous_draft=previous_draft,
                    reviewer_feedback=reviewer_feedback,
                    context=context
                )
            else:
                prompt = DRAFT_GENERATION_PROMPT.format(
                    subject=subject,
                    description=description,
                    category=category,
                    context=context
                )
            
            messages = [HumanMessage(content=prompt)]
            response = await self.llm.ainvoke(messages)
            
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Draft generation error: {e}")
            return "I apologize, but I'm experiencing technical difficulties. Please contact our support team directly for assistance."
    
    async def review_draft(
        self, 
        subject: str, 
        description: str, 
        category: str,
        draft_response: str, 
        context: str
    ) -> Dict[str, Any]:
        """Review draft response for quality and compliance"""
        from prompts.review import REVIEW_PROMPT
        
        try:
            prompt = REVIEW_PROMPT.format(
                subject=subject,
                description=description,
                category=category,
                draft_response=draft_response,
                context=context
            )
            
            messages = [
                SystemMessage(content="You are a quality assurance reviewer. Always respond with valid JSON."),
                HumanMessage(content=prompt)
            ]
            response = await self.llm.ainvoke(messages)
            
            # Clean up response content
            content = response.content.strip()
            # Try to find JSON in the response if it's wrapped in other text
            if not content.startswith('{'):
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    content = json_match.group(0)
            
            try:
                # Parse JSON response
                result = json.loads(content)
                # Validate required fields
                required_fields = {"approved", "score", "feedback", "issues"}
                if not all(field in result for field in required_fields):
                    raise ValueError("Missing required fields in response")
                return result
            except json.JSONDecodeError as je:
                logger.error(f"Failed to parse review response as JSON: {je}\nResponse: {content}")
                raise
            
        except Exception as e:
            logger.error(f"Review error: {e}")
            # Fallback approval for system errors
            return {
                "approved": True,
                "score": 0.7,
                "feedback": f"System error during review ({str(e)}), auto-approved",
                "issues": []
            }