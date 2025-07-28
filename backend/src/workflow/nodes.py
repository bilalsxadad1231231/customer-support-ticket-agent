# workflow/nodes.py
import logging
from datetime import datetime
from typing import Dict, Any
from src.workflow.state import SupportAgentState, SupportTicket, ClassificationResult, RAGResult, ReviewResult, DraftResponse
from src.services.llm_service import LLMService
from src.services.vector_store import VectorStoreService
from src.utils.logger import log_escalation

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
    
    def _create_fallback_draft(self, state: SupportAgentState, message: str = None) -> DraftResponse:
        """Create a fallback draft response"""
        if message is None:
            message = "I apologize, but I'm experiencing technical difficulties. Please contact our support team directly."
        
        return DraftResponse(
            content=message,
            version=len(state["all_drafts"]) + 1,
            timestamp=datetime.now().isoformat()
        )
    
    async def input_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Entry point - process input ticket"""
        logger.info(f"[INPUT_NODE] Processing ticket: {state['ticket']['ticket_id']}")
        
        if not state["ticket"]:
            logger.error("No ticket found in initial state")
            raise ValueError("No ticket found in initial state")
        
        # Set processing start time
        start_time = datetime.now().isoformat()
        ticket = SupportTicket(
            subject=state["ticket"]["subject"],
            description=state["ticket"]["description"],
            ticket_id=state["ticket"]["ticket_id"]
        )

        logger.info(f"[INPUT_NODE] Ticket initialized - Subject: {ticket.subject[:50]}...")
        
        return {
            "ticket": ticket,
            "processing_start_time": start_time,
            "retry_count": 0,
            "all_drafts": [],
            "all_reviews": []
        }
    
    async def classification_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Classify the support ticket"""
        logger.info(f"[CLASSIFICATION_NODE] Classifying ticket: {state['ticket'].ticket_id}")
        
        if not state["ticket"]:
            raise ValueError("No ticket found in state")
        
        try:
            result = await self.llm_service.classify_ticket(
                subject=state["ticket"].subject,
                description=state["ticket"].description
            )
            
            classification = ClassificationResult(
                category=result["category"],
                confidence=result["confidence"],
                reasoning=result["reasoning"]
            )
            
            logger.info(f"[CLASSIFICATION_NODE] Classified as: {classification.category} (confidence: {classification.confidence})")
            
            return {"classification": classification}
            
        except Exception as e:
            logger.error(f"[CLASSIFICATION_NODE] Classification failed: {e}")
            # Fallback classification
            classification = ClassificationResult(
                category="general",
                confidence=0.5,
                reasoning=str(e)
            )
            return {"classification": classification}
    
    async def rag_retrieval_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Retrieve relevant context using RAG"""
        logger.info(f"[RAG_NODE] Retrieving context for category: {state['classification'].category}")
        
        await self._ensure_initialized()
        
        if not state["ticket"] or not state["classification"]:
            raise ValueError("Missing ticket or classification in state")
        
        # Create search query from ticket
        query = f"{state['ticket'].subject} {state['ticket'].description}"
        
        try:
            result = await self.vector_service.search(
                query=query,
                category=state["classification"].category,
                k=5
            )

            rag_result = RAGResult(
                documents=result["documents"],
                metadata=result["metadata"],
                query_used=result['metadata']['query_used']
            )
            
            logger.info(f"[RAG_NODE] Retrieved {len(rag_result.documents)} documents")
            
            return {"rag_results": rag_result}
            
        except Exception as e:
            logger.error(f"[RAG_NODE] RAG retrieval failed: {e}")
            # Fallback context
            fallback_result = RAGResult(
                documents=[f"General assistance for {state['classification'].category} issues. Please contact support for specific help."],
                metadata={"category": state['classification'].category, "error": str(e)},
                query_used=query
            )
            return {"rag_results": fallback_result}
    
    async def draft_generation_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Generate initial response draft"""
        logger.info(f"[DRAFT_NODE] Generating draft for ticket: {state['ticket'].ticket_id}")
        
        if not all([state['ticket'], state['classification'], state['rag_results']]):
            raise ValueError("Missing required state for draft generation")
        
        # Prepare context from RAG results
        context = "\n".join(state['rag_results'].documents)
        
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
            
            logger.info(f"[DRAFT_NODE] Generated draft v{draft.version} ({len(draft_content)} chars)")
            
            return {
                "current_draft": draft,
                "all_drafts": updated_drafts
            }
            
        except Exception as e:
            logger.error(f"[DRAFT_NODE] Draft generation failed: {e}")
            # Fallback draft
            draft = self._create_fallback_draft(state)
            return { 
                "current_draft": draft,
                "all_drafts": state["all_drafts"] + [draft]
            }
    
    async def review_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Review the draft response"""
        logger.info(f"[REVIEW_NODE] Reviewing draft v{state['current_draft'].version}")
        
        if not all([state['ticket'], state['classification'], state['current_draft'], state['rag_results']]):
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
            
            logger.info(f"[REVIEW_NODE] Review result: {'APPROVED' if review.approved else 'REJECTED'} (score: {review.score})")
            
            return {
                "review_result": review,
                "all_reviews": updated_reviews
            }
            
        except Exception as e:
            logger.error(f"[REVIEW_NODE] Review failed: {e}")
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
    
    async def generate_queries_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Generate refined search queries based on review feedback"""
        logger.info(f"[QUERY_NODE] Generating refined queries based on feedback")
        
        if not all([state['ticket'], state['classification'], state['review_result']]):
            raise ValueError("Missing required state for query generation")
        
        query = f"{state['ticket'].subject} {state['ticket'].description}"
        
        try:
            # Extract key points from review feedback
            feedback = state["review_result"].feedback
            issues = state["review_result"].issues
            
            # Generate refined queries using LLM
            result = await self.llm_service.generate_refined_queries(
                query=query,
                category=state["classification"].category,
                feedback=feedback,
            )
            
            logger.info(f"[QUERY_NODE] Generated {len(result)} refined queries")
            
            return {
                "refined_queries": result
            }
            
        except Exception as e:
            logger.error(f"[QUERY_NODE] Query generation failed: {e}")
            # Fallback to basic query
            return {
                "refined_queries": [query]
            }
    
    async def context_refinement_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Refine context based on reviewer feedback"""
        logger.info(f"[REFINEMENT_NODE] Refining context with {len(state['refined_queries'])} queries")
        
        await self._ensure_initialized()
        
        if not all([state['ticket'], state['classification'], state['review_result'], state['refined_queries']]):
            raise ValueError("Missing required state for context refinement")
        
        try:
            # Use the improved refine_search that handles multiple queries
            result = await self.vector_service.refine_search(
                queries=state['refined_queries'],
                category=state['classification'].category,
                k=3  # Number of results per query
            )
            
            refined_rag_result = RAGResult(
                documents=result['documents'],
                metadata=result['metadata'],
                query_used=result['metadata'].get('query_used', '')
            )
            
            logger.info(f"[REFINEMENT_NODE] Refined context: {len(refined_rag_result.documents)} documents")
            
            return {"refined_rag_results": refined_rag_result}
            
        except Exception as e:
            logger.error(f"[REFINEMENT_NODE] Context refinement failed: {e}")
            # Fall back to original results
            return {"refined_rag_results": state["rag_results"]}
    
    async def redraft_generation_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Generate improved response based on feedback"""
        logger.info(f"[REDRAFT_NODE] Generating redraft (retry {state['retry_count'] + 1})")
        
        if not all([state["ticket"], state["classification"], state["current_draft"], 
                   state["review_result"], state["refined_rag_results"]]):
            raise ValueError("Missing required state for redraft generation")
        
        # Use refined context
        context = "\n".join(state['refined_rag_results'].documents)
        
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
            
            logger.info(f"[REDRAFT_NODE] Generated redraft v{draft.version} ({len(draft_content)} chars)")
            
            return {
                "current_draft": draft,
                "all_drafts": updated_drafts,
                "retry_count": retry_count
            }
            
        except Exception as e:
            logger.error(f"[REDRAFT_NODE] Redraft generation failed: {e}")
            # Fallback redraft
            draft = self._create_fallback_draft(
                state, 
                "I apologize for the confusion. Let me connect you with a human agent for better assistance."
            )
            return {
                "current_draft": draft,
                "all_drafts": state["all_drafts"] + [draft],
                "retry_count": state["retry_count"] + 1
            }
    
    async def escalation_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Handle escalation when max retries exceeded"""
        logger.warning(f"[ESCALATION_NODE] Escalating ticket: {state['ticket'].ticket_id} (retries: {state['retry_count']})")
        
        escalation_reason = "Maximum retry attempts exceeded without approval"
        
        # Log escalation
        await log_escalation(
            ticket=state['ticket'],
            classification=state['classification'],
            all_drafts=state['all_drafts'],
            all_reviews=state['all_reviews'],
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
        
        logger.info(f"[ESCALATION_NODE] Ticket escalated after {processing_time:.2f}s")
        
        return {
            "escalated": True,
            "escalation_reason": escalation_reason,
            "final_response": escalation_message,
            "processing_end_time": end_time,
            "total_processing_time": processing_time
        }
    
    async def final_output_node(self, state: SupportAgentState) -> Dict[str, Any]:
        """Generate final approved response"""
        logger.info(f"[FINAL_NODE] Generating final output for ticket: {state['ticket'].ticket_id}")
        
        if not state["current_draft"]:
            raise ValueError("No current draft for final output")
        
        end_time = datetime.now().isoformat()
        processing_time = (
            datetime.fromisoformat(end_time) - 
            datetime.fromisoformat(state["processing_start_time"])
        ).total_seconds() if state["processing_start_time"] else 0
        
        logger.info(f"[FINAL_NODE] Ticket resolved successfully in {processing_time:.2f}s")
        
        return {
            "final_response": state["current_draft"].content,
            "processing_end_time": end_time,
            "total_processing_time": processing_time
        }
