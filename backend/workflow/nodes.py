# workflow/nodes.py
from csv import QUOTE_STRINGS
import logging
import asyncio
from datetime import datetime
from operator import truediv
from typing import Dict, Any
from workflow.state import SupportAgentState, SupportTicket, ClassificationResult, RAGResult, ReviewResult, DraftResponse
from services.llm_service import LLMService
from services.vector_store import VectorStoreService
from utils.logger import log_escalation

logger = logging.getLogger(__name__)

class SupportNodes:
    def __init__(self):
        self.llm_service = LLMService()
        self.vector_service = VectorStoreService()
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure vector stores are initialized"""
        if not self._initialized:
            self.vector_service
            self._initialized = True
    
    async def input_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Entry point - process input ticket"""
        logger.info("Processing input ticket")
        
        logger.info(f"Ticket: {state['ticket']}")
        if not state["ticket"]:
            logger.error("No ticket found in initial state")
            raise ValueError("No ticket found in initial state")
        
        # Set processing start time
        start_time = datetime.now().isoformat()
        
        return {
            "ticket": state["ticket"],  # Preserve the ticket
            "processing_start_time": start_time,
            "retry_count": 0,
            "all_drafts": [],
            "all_reviews": []
        }
    
    async def classification_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Classify the support ticket"""
        logger.info("Classifying ticket")
        
        if not state["ticket"]:
            raise ValueError("No ticket found in state")
        
        try:
            result = await self.llm_service.classify_ticket(
                state["ticket"].subject,
                state["ticket"].description
            )
            
            logger.info(f"Classification result: {result}")
            
            classification = ClassificationResult(
                category=result["category"],
                confidence=result["confidence"],
                reasoning=result["reasoning"]
            )
            
            logger.info(f"Classified as: {classification.category} (confidence: {classification.confidence})")
            
            return {"classification": classification}
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            # Fallback classification
            classification = ClassificationResult(
                category="general",
                confidence=0.5,
                reasoning="Classification error, defaulted to general"
            )
            return {"classification": classification}
    
    async def rag_retrieval_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Retrieve relevant context using RAG"""
        logger.info("Retrieving context via RAG")
        
        await self._ensure_initialized()
        
        if not state["ticket"] or not state["classification"]:
            raise ValueError("Missing ticket or classification in state")
        
        # Create search query from ticket
        query = f"{state['ticket'].subject} {state['ticket'].description}"
        category = state["classification"].category
        
        try:
            logger.info(f"Query: {query}")
            result = await self.vector_service.search(
                query=query,
                category=category,
                k=5
            )
            
            logger.info(f"Result: {result}")

            rag_result = RAGResult(
                documents=result["documents"],
                metadata=result["metadata"],
                query_used=result['metadata']['query_used']
            )
            
            logger.info(f"Retrieved {len(rag_result.documents)} documents for {category}")
            
            return {"rag_results": rag_result}
            
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            # Fallback context
            fallback_result = RAGResult(
                documents=[f"General assistance for {category} issues. Please contact support for specific help."],
                metadata={"category": category, "error": str(e)},
                query_used=query
            )
            return {"rag_results": fallback_result}
    
    async def draft_generation_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Generate initial response draft"""
        logger.info("Generating response draft")
        
        if not all([state["ticket"], state["classification"], state["rag_results"]]):
            raise ValueError("Missing required state for draft generation")
        
        # Prepare context from RAG results
        context = "\n".join(state["rag_results"].documents)
        
        try:
            draft_content = await self.llm_service.generate_draft(
                subject=state["ticket"].subject,
                description=state["ticket"].description,
                category=state["classification"].category,
                context=context
            )
            
            draft = DraftResponse(
                content=draft_content,
                version=len(state["all_drafts"]) + 1,
                timestamp=datetime.now().isoformat()
            )
            
            # Update drafts list
            updated_drafts = state["all_drafts"] + [draft]
            
            logger.info(f"Generated draft version {draft.version}")
            
            return {
                "current_draft": draft,
                "all_drafts": updated_drafts
            }
            
        except Exception as e:
            logger.error(f"Draft generation failed: {e}")
            # Fallback draft
            draft = DraftResponse(
                content="I apologize, but I'm experiencing technical difficulties. Please contact our support team directly.",
                version=len(state["all_drafts"]) + 1,
                timestamp=datetime.now().isoformat()
            )
            return { 
                "current_draft": draft,
                "all_drafts": state["all_drafts"] + [draft]
            }
    
    async def review_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Review the draft response"""
        logger.info("Reviewing draft response")
        
        if not all([state["ticket"], state["classification"], state["current_draft"], state["rag_results"]]):
            raise ValueError("Missing required state for review")
        
        context = "\n".join(state["rag_results"].documents)
        
        try:
            result = await self.llm_service.review_draft(
                subject=state["ticket"].subject,
                description=state["ticket"].description,
                category=state["classification"].category,
                draft_response=state["current_draft"].content,
                context=context
            )
            
            review = ReviewResult(
                approved=result["approved"],
                feedback=result["feedback"],
                score=result["score"],
                issues=result["issues"]
            )
            
            # Update reviews list
            updated_reviews = state["all_reviews"] + [review]
            
            logger.info(f"Review completed: {'APPROVED' if review.approved else 'REJECTED'} (score: {review.score})")
            
            return {
                "review_result": review,
                "all_reviews": updated_reviews
            }
            
        except Exception as e:
            logger.error(f"Review failed: {e}")
            # Fallback approval on system error
            review = ReviewResult(
                approved=True,
                feedback="System error during review, auto-approved",
                score=0.7,
                issues=[]
            )
            return {
                "review_result": review,
                "all_reviews": state["all_reviews"] + [review]
            }
    
    async def context_refinement_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Refine context based on reviewer feedback"""
        logger.info("Refining context based on feedback")
        
        await self._ensure_initialized()
        
        if not all([state["ticket"], state["classification"], state["review_result"]]):
            raise ValueError("Missing required state for context refinement")
        
        # Create refined query based on feedback
        original_query = f"{state['ticket'].subject} {state['ticket'].description}"
        feedback = state["review_result"].feedback
        
        try:
            result = await self.vector_service.refine_search(
                original_query=original_query,
                category=state["classification"].category,
                feedback=feedback,
                k=7  # Get more results for retry
            )
            
            refined_rag_result = RAGResult(
                documents=result["documents"],
                metadata=result["metadata"],
                query_used=result["query_used"]
            )
            
            logger.info(f"Refined context: {len(refined_rag_result.documents)} documents")
            
            return {"refined_rag_results": refined_rag_result}
            
        except Exception as e:
            logger.error(f"Context refinement failed: {e}")
            # Fall back to original results
            return {"refined_rag_results": state["rag_results"]}
    
    async def redraft_generation_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Generate improved response based on feedback"""
        logger.info("Generating improved response")
        
        if not all([state["ticket"], state["classification"], state["current_draft"], 
                   state["review_result"], state["refined_rag_results"]]):
            raise ValueError("Missing required state for redraft generation")
        
        # Use refined context
        context = "\n".join(state["refined_rag_results"].documents)
        
        try:
            draft_content = await self.llm_service.generate_draft(
                subject=state["ticket"].subject,
                description=state["ticket"].description,
                category=state["classification"].category,
                context=context,
                is_redraft=True,
                previous_draft=state["current_draft"].content,
                reviewer_feedback=state["review_result"].feedback
            )
            
            draft = DraftResponse(
                content=draft_content,
                version=len(state["all_drafts"]) + 1,
                timestamp=datetime.now().isoformat()
            )
            
            # Update drafts list
            updated_drafts = state["all_drafts"] + [draft]
            # Increment retry count
            retry_count = state["retry_count"] + 1
            
            logger.info(f"Generated redraft version {draft.version} (retry {retry_count})")
            
            return {
                "current_draft": draft,
                "all_drafts": updated_drafts,
                "retry_count": retry_count
            }
            
        except Exception as e:
            logger.error(f"Redraft generation failed: {e}")
            # Fallback redraft
            draft = DraftResponse(
                content="I apologize for the confusion. Let me connect you with a human agent for better assistance.",
                version=len(state["all_drafts"]) + 1,
                timestamp=datetime.now().isoformat()
            )
            return {
                "current_draft": draft,
                "all_drafts": state["all_drafts"] + [draft],
                "retry_count": state["retry_count"] + 1
            }
    
    async def escalation_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Handle escalation when max retries exceeded"""
        logger.info("Escalating ticket to human review")
        
        escalation_reason = "Maximum retry attempts exceeded without approval"
        
        # Log escalation
        await log_escalation(
            ticket=state["ticket"],
            classification=state["classification"],
            all_drafts=state["all_drafts"],
            all_reviews=state["all_reviews"],
            reason=escalation_reason
        )
        
        escalation_message = (
            "I apologize, but your request requires human review to ensure we provide "
            "the most accurate assistance. A support specialist will review your case "
            "and respond within 24 hours. Thank you for your patience."
        )
        
        end_time = datetime.now().isoformat()
        processing_time = (
            datetime.fromisoformat(end_time) - 
            datetime.fromisoformat(state["processing_start_time"])
        ).total_seconds() if state["processing_start_time"] else 0
        
        return {
            "escalated": True,
            "escalation_reason": escalation_reason,
            "final_response": escalation_message,
            "processing_end_time": end_time,
            "total_processing_time": processing_time
        }
    
    async def final_output_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Generate final approved response"""
        logger.info("Generating final output")
        
        if not state["current_draft"]:
            raise ValueError("No current draft for final output")
        
        end_time = datetime.now().isoformat()
        processing_time = (
            datetime.fromisoformat(end_time) - 
            datetime.fromisoformat(state["processing_start_time"])
        ).total_seconds() if state["processing_start_time"] else 0
        
        logger.info(f"Support ticket resolved successfully in {processing_time:.2f} seconds")
        
        return {
            "final_response": state["current_draft"].content,
            "processing_end_time": end_time,
            "total_processing_time": processing_time
        }