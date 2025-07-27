# workflow/edges.py
import logging
from typing import Literal, Dict, Any
from src.workflow.state import SupportAgentState
from src.config.settings import settings

logger = logging.getLogger(__name__)

class SupportEdges:
    """Edge conditions and routing logic for the support agent graph"""
    
    @staticmethod
    def should_retry(state: SupportAgentState) -> Literal["retry", "escalate", "output"]:
        """Determine if we should retry, escalate, or output final response"""
        
        # If no review result, something went wrong - escalate
        if not state["review_result"]:
            logger.warning("No review result found, escalating")
            return "escalate"
        
        # If approved, output final response
        if state["review_result"].approved:
            logger.info("Draft approved, proceeding to final output")
            return "output"
        
        # If max retries reached, escalate
        if state["retry_count"] >= settings.MAX_RETRIES:
            logger.info(f"Max retries ({settings.MAX_RETRIES}) reached, escalating")
            return "escalate"
        
        # Otherwise, retry
        logger.info(f"Draft rejected, retrying (attempt {state['retry_count'] + 1}/{settings.MAX_RETRIES})")
        return "retry"
    
    @staticmethod
    def is_processing_complete(state: SupportAgentState) -> bool:
        """Check if processing is complete (either resolved or escalated)"""
        return state["final_response"] is not None or state["escalated"]
    
    @staticmethod
    def needs_context_refinement(state: SupportAgentState) -> bool:
        """Check if context refinement is needed for retry"""
        return (
            state["review_result"] is not None and 
            not state["review_result"].approved and 
            state["retry_count"] < settings.MAX_RETRIES
        )
    
    @staticmethod
    def validate_state_transition(from_node: str, to_node: str, state: SupportAgentState) -> bool:
        """Validate that state transition is valid"""
        
        required_state = {
            "classification": ["ticket"],
            "rag_retrieval": ["ticket", "classification"],
            "draft_generation": ["ticket", "classification", "rag_results"],
            "review": ["ticket", "classification", "current_draft"],
            "context_refinement": ["ticket", "classification", "review_result"],
            "redraft_generation": ["ticket", "classification", "review_result", "refined_rag_results"],
            "escalation": ["ticket"],
            "final_output": ["current_draft"]
        }
        
        if to_node in required_state:
            for required_field in required_state[to_node]:
                if required_field not in state or state[required_field] is None:
                    logger.error(f"Missing required field {required_field} for transition to {to_node}")
                    return False
        
        return True

# Edge condition functions for LangGraph
def review_decision(state: SupportAgentState) -> str:
    """Edge condition function to determine next step after review"""
    return SupportEdges.should_retry(state)

 