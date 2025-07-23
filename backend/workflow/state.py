# workflow/state.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from langgraph.graph import MessagesState

class SupportTicket(BaseModel):
    subject: str
    description: str
    ticket_id: Optional[str] = None

class ClassificationResult(BaseModel):
    category: str
    confidence: float
    reasoning: str

class RAGResult(BaseModel):
    documents: List[str]
    metadata: Dict[str, Any]
    query_used: str

class ReviewResult(BaseModel):
    approved: bool
    feedback: str
    score: float
    issues: List[str]

class DraftResponse(BaseModel):
    content: str
    version: int
    timestamp: str

class SupportAgentState(MessagesState):
    # Input
    ticket: Optional[SupportTicket] = None
    
    # Classification
    classification: Optional[ClassificationResult] = None
    
    # RAG Results
    rag_results: Optional[RAGResult] = None
    refined_rag_results: Optional[RAGResult] = None
    
    # Draft Generation
    current_draft: Optional[DraftResponse] = None
    all_drafts: List[DraftResponse] = []
    
    # Review Process
    review_result: Optional[ReviewResult] = None
    all_reviews: List[ReviewResult] = []
    
    # Retry Logic
    retry_count: int = 0
    max_retries: int = 2
    
    # Final Output
    final_response: Optional[str] = None
    escalated: bool = False
    escalation_reason: Optional[str] = None
    
    # Metadata
    processing_start_time: Optional[str] = None
    processing_end_time: Optional[str] = None
    total_processing_time: Optional[float] = None