# workflow/graph.py
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

from src.workflow.state import SupportAgentState, SupportTicket
from src.workflow.nodes import SupportNodes
from src.workflow.edges import review_decision

logger = logging.getLogger(__name__)

class SupportAgentGraph:
    """Main support agent graph orchestrator"""
    
    def __init__(self):
        self.nodes = SupportNodes()
        self.graph = None
        self.app = None
        self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph workflow"""
        
        # Create the graph
        self.graph = StateGraph(SupportAgentState)
        
        # Add nodes
        self.graph.add_node("input", self.nodes.input_node)
        self.graph.add_node("classification", self.nodes.classification_node)
        self.graph.add_node("rag_retrieval", self.nodes.rag_retrieval_node)
        self.graph.add_node("draft_generation", self.nodes.draft_generation_node)
        self.graph.add_node("review", self.nodes.review_node)
        self.graph.add_node("generate_queries", self.nodes.generate_queries_node)
        self.graph.add_node("context_refinement", self.nodes.context_refinement_node)
        self.graph.add_node("redraft_generation", self.nodes.redraft_generation_node)
        self.graph.add_node("escalation", self.nodes.escalation_node)
        self.graph.add_node("final_output", self.nodes.final_output_node)
        
        # Set entry point
        self.graph.set_entry_point("input")
        
        # Add edges - Linear flow first
        self.graph.add_edge("input", "classification")
        self.graph.add_edge("classification", "rag_retrieval")
        self.graph.add_edge("rag_retrieval", "draft_generation")
        self.graph.add_edge("draft_generation", "review")
        
        # Conditional edge after review
        self.graph.add_conditional_edges(
            "review",
            review_decision,
            {
                "retry": "generate_queries",  # Updated to point to new node
                "escalate": "escalation", 
                "output": "final_output"
            }
        )
        
        # Retry flow with generate_queries
        self.graph.add_edge("generate_queries", "context_refinement")
        self.graph.add_edge("context_refinement", "redraft_generation")
        self.graph.add_edge("redraft_generation", "review")
        
        # End nodes
        self.graph.add_edge("escalation", END)
        self.graph.add_edge("final_output", END)
        
        # Compile with checkpointer for persistence
        memory = InMemorySaver()
        self.app = self.graph.compile()
        
        logger.info("Support agent graph compiled successfully")
    
    async def process_ticket(
        self, 
        subject: str, 
        description: str, 
        ticket_id: str = None
    ) -> Dict[str, Any]:
        """Process a support ticket through the graph"""
        
        logger.info(f"Processing ticket: {subject}")
        
        # Create initial state
        ticket = SupportTicket(
            subject=subject,
            description=description,
            ticket_id=ticket_id
        )
        
        initial_state = SupportAgentState(
            ticket=ticket,
            messages=[]
        )
        
        try:
            # Run the graph
            config = {"configurable": {"thread_id": ticket_id or "default"}}
            
            result = await self.app.ainvoke(initial_state, config=config)
            
            # Extract relevant response data
            response = {
                "ticket_id": ticket_id,
                "subject": subject,
                "description": description,
                "category": result.classification.category if result.classification else "unknown",
                "final_response": result.final_response,
                "escalated": result.escalated or False,
                "retry_count": result.retry_count,
                "processing_time": result.total_processing_time,
                "drafts_generated": len(result.all_drafts),
                "reviews_conducted": len(result.all_reviews)
            }
            
            if result.escalated:
                response["escalation_reason"] = result.escalation_reason
            
            logger.info(f"Ticket processed successfully: {'escalated' if result.escalated else 'resolved'}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing ticket: {e}")
            return {
                "ticket_id": ticket_id,
                "subject": subject, 
                "description": description,
                "error": str(e),
                "final_response": "We apologize, but there was an error processing your request. Please contact support directly.",
                "escalated": True,
                "escalation_reason": f"System error: {str(e)}"
            }
    
    def get_graph_visualization(self) -> str:
        """Get a text representation of the graph structure"""
        
        visualization = """
Support Agent Graph Structure:
=============================

[Input] → [Classification] → [RAG Retrieval] → [Draft Generation] → [Review]
                                                                         ↓
[Final Output] ←← [Approved?] ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
      ↑                 ↓ [Rejected & Retries < Max]
      ↑                 ↓
[Escalation] ←← [Max Retries?] ←← [Generate Queries] → [Context Refinement] → [Redraft Generation]
                                              ↑                    ↓
                                              ←←←←←←← [Review] ←←←←←

Key Features:
- Maximum 2 retry attempts
- Query generation based on reviewer feedback
- Context refinement using generated queries
- Automatic escalation when retries exhausted
- Full audit trail of all drafts and reviews
- Category-specific RAG retrieval
"""
        return visualization
    
    async def get_processing_history(self, ticket_id: str) -> Dict[str, Any]:
        """Get processing history for a ticket"""
        
        try:
            config = {"configurable": {"thread_id": ticket_id}}
            
            # Get current state
            state = await self.app.aget_state(config)
            
            if not state or not state.values:
                return {"error": "No processing history found for ticket"}
            
            values = state.values
            
            history = {
                "ticket_id": ticket_id,
                "classification": values.get("classification"),
                "drafts": values.get("all_drafts", []),
                "reviews": values.get("all_reviews", []), 
                "retry_count": values.get("retry_count", 0),
                "escalated": values.get("escalated", False),
                "final_response": values.get("final_response"),
                "processing_time": values.get("total_processing_time")
            }
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting processing history: {e}")
            return {"error": str(e)}


graph = SupportAgentGraph().app
