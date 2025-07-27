# services/llm_service.py
import json
import logging
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from src.config.settings import settings
from src.prompts.query_refinement import QUERY_REFINEMENT_PROMPT

logger = logging.getLogger(__name__)

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
        from src.prompts.classification import CLASSIFICATION_PROMPT
        
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
        from src.prompts.draft_generation import DRAFT_GENERATION_PROMPT, REDRAFT_PROMPT
        
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
        from src.prompts.review import REVIEW_PROMPT
        
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

# services/llm_service.py - Add this function to your LLMService class

    async def generate_refined_queries(
        self, 
        query: str,
        category: str, 
        feedback: str,
    ) -> List[str]:
        """
        Generate refined search queries based on reviewer feedback.
        
        Args:
            subject: Original ticket subject
            description: Original ticket description  
            category: Ticket category
            feedback: Reviewer feedback explaining why initial response was inadequate
            
        Returns:
            List of refined search queries
        """
        logger.info(f"Generating refined queries based on feedback")
        try:
            logger.info(f"Query: {query}")

            prompt = QUERY_REFINEMENT_PROMPT.format(
                query=query,
                category=category,
                feedback=feedback,
            )
            logger.info(f"Prompt: prompt template here")

            messages = [
                SystemMessage(content="You are an expert at analyzing feedback and generating better search queries. Always respond with valid JSON."),
                HumanMessage(content=prompt)
            ]
            logger.info(f"Prompt: {prompt}")

            response = await self.llm.ainvoke(messages)
            content = response.content.strip()
            
            logger.info(f"Response: {response}")
            # Clean up response content to extract JSON
            if not content.startswith('{'):
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    content = json_match.group(0)
            
            try:
                result = json.loads(content)
                
                # Validate response structure
                if "refined_queries" not in result:
                    raise ValueError("Missing 'refined_queries' in response")
                
                queries = result["refined_queries"]
                
                # Ensure we have valid queries
                if not isinstance(queries, list) or len(queries) == 0:
                    raise ValueError("Invalid or empty queries list")
                
                # Filter out empty or very short queries
                valid_queries = [q.strip() for q in queries if isinstance(q, str) and len(q.strip()) > 3]
                
                if not valid_queries:
                    raise ValueError("No valid queries generated")
                
                logger.info(f"Generated {len(valid_queries)} refined queries based on feedback")
                logger.debug(f"Analysis: {result.get('analysis', {})}")
                
                # Return max 5 queries to avoid too many searches
                return valid_queries[:5]
                
            except json.JSONDecodeError as je:
                logger.error(f"Failed to parse query refinement response as JSON: {je}\nResponse: {content}")
                raise
                
        except Exception as e:
            logger.error(f"Query refinement error: {e}")
            
            # Fallback: Create basic refined queries using simple heuristics
            fallback_queries = []
            
            # Extract key terms from feedback for basic refinement
            feedback_words = feedback.lower().split()
            important_words = [word for word in feedback_words 
                            if len(word) > 4 and word not in ['should', 'would', 'could', 'might', 'about', 'better']]
            
            # Generate fallback queries
            base_query = f"{subject} {description}".strip()
            
            fallback_queries.append(f"how to {base_query}")
            fallback_queries.append(f"troubleshoot {base_query}")
            fallback_queries.append(f"fix {base_query}")
            
            if important_words:
                fallback_queries.append(f"{base_query} {' '.join(important_words[:2])}")
            
            fallback_queries.append(f"step by step {base_query}")
            
            logger.warning(f"Using fallback queries due to error in query generation")
            return fallback_queries[:4]