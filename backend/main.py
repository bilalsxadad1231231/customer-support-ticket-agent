# main.py
import asyncio
import logging
import uuid
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from workflow.graph import SupportAgentGraph
from utils.validators import TicketValidator
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Support Ticket Resolution Agent",
    description="AI-powered support agent using LangGraph",
    version="1.0.0"
)

# Initialize graph
support_graph = None

class TicketRequest(BaseModel):
    subject: str
    description: str
    ticket_id: str = None

class TicketResponse(BaseModel):
    ticket_id: str
    subject: str
    description: str
    category: str
    final_response: str
    escalated: bool
    retry_count: int
    processing_time: float
    drafts_generated: int
    reviews_conducted: int
    escalation_reason: str = None
    error: str = None

@app.on_event("startup")
async def startup_event():
    """Initialize the support agent graph on startup"""
    global support_graph
    
    try:
        logger.info("Initializing support agent graph...")
        support_graph = SupportAgentGraph()
        logger.info("Support agent graph initialized successfully")
        
        # Initialize vector stores
        await support_graph.nodes.vector_service.initialize_vector_stores()
        logger.info("Vector stores initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize support agent: {e}")
        raise

@app.post("/process_ticket", response_model=TicketResponse)
async def process_ticket(request: TicketRequest) -> TicketResponse:
    """Process a support ticket"""
    
    try:
        # Validate input
        validation = TicketValidator.validate_ticket_input(
            request.subject, 
            request.description
        )
        
        if not validation["valid"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid input: {', '.join(validation['errors'])}"
            )
        
        # Generate ticket ID if not provided
        ticket_id = request.ticket_id or str(uuid.uuid4())
        
        # Process ticket
        result = await support_graph.process_ticket(
            subject=validation["cleaned_subject"],
            description=validation["cleaned_description"],
            ticket_id=ticket_id
        )
        
        return TicketResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ticket/{ticket_id}/history")
async def get_ticket_history(ticket_id: str) -> Dict[str, Any]:
    """Get processing history for a ticket"""
    
    try:
        history = await support_graph.get_processing_history(ticket_id)
        return history
        
    except Exception as e:
        logger.error(f"Error getting ticket history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph/structure")
async def get_graph_structure() -> Dict[str, str]:
    """Get graph structure visualization"""
    
    return {
        "structure": support_graph.get_graph_visualization()
    }

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "graph_initialized": support_graph is not None
    }

# CLI interface for development
async def cli_interface():
    """Command line interface for testing"""
    
    print("Support Ticket Resolution Agent - CLI Interface")
    print("=" * 50)
    
    # Initialize graph
    global support_graph
    support_graph = SupportAgentGraph()
    await support_graph.nodes.vector_service.initialize_vector_stores()
    
    print("Graph initialized successfully!")
    print("Enter 'quit' to exit\n")
    
    while True:
        try:
            print("\n" + "-" * 30)
            subject = input("Enter ticket subject: ").strip()
            
            if subject.lower() == 'quit':
                break
            
            if not subject:
                print("Subject cannot be empty!")
                continue
            
            description = input("Enter ticket description: ").strip()
            
            if not description:
                print("Description cannot be empty!")
                continue
            
            # Validate input
            validation = TicketValidator.validate_ticket_input(subject, description)
            
            if not validation["valid"]:
                print(f"Invalid input: {', '.join(validation['errors'])}")
                continue
            
            print("\nProcessing ticket...")
            
            # Process ticket
            result = await support_graph.process_ticket(
                subject=validation["cleaned_subject"],
                description=validation["cleaned_description"],
                ticket_id=str(uuid.uuid4())
            )
            
            # Display results
            print("\n" + "=" * 50)
            print("TICKET PROCESSING RESULTS")
            print("=" * 50)
            print(f"Category: {result['category']}")
            print(f"Escalated: {result['escalated']}")
            print(f"Retry Count: {result['retry_count']}")
            print(f"Processing Time: {result['processing_time']:.2f}s")
            print(f"Drafts Generated: {result['drafts_generated']}")
            print(f"Reviews Conducted: {result['reviews_conducted']}")
            
            if result['escalated']:
                print(f"Escalation Reason: {result['escalation_reason']}")
            
            print("\nFINAL RESPONSE:")
            print("-" * 20)
            print(result['final_response'])
            print("=" * 50)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        asyncio.run(cli_interface())
    else:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)