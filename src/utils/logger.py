# utils/logger.py
import os
import csv
import logging
import asyncio
from datetime import datetime
from typing import List, Optional
from src.workflow.state import SupportTicket, ClassificationResult, DraftResponse, ReviewResult
from src.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('support_agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def log_escalation(
    ticket: SupportTicket,
    classification: Optional[ClassificationResult],
    all_drafts: List[DraftResponse],
    all_reviews: List[ReviewResult],
    reason: str
):
    """Log escalated ticket to CSV file"""
    
    try:
        async def write_to_csv():
            # Create directory if it doesn't exist
            await asyncio.to_thread(
                os.makedirs,
                os.path.dirname(settings.ESCALATION_LOG_PATH),
                exist_ok=True
            )
            
            # Check if file exists to determine if we need headers
            file_exists = await asyncio.to_thread(os.path.exists, settings.ESCALATION_LOG_PATH)
            
            # Prepare escalation data
            escalation_data = {
                'timestamp': datetime.now().isoformat(),
                'ticket_id': ticket.ticket_id or 'unknown',
                'subject': ticket.subject,
                'description': ticket.description,
                'category': classification.category if classification else 'unknown',
                'classification_confidence': classification.confidence if classification else 0.0,
                'num_drafts': len(all_drafts),
                'num_reviews': len(all_reviews),
                'final_review_score': all_reviews[-1].score if all_reviews else 0.0,
                'escalation_reason': reason,
                'failed_drafts': ' | '.join([draft.content[:100] + '...' for draft in all_drafts]),
                'reviewer_feedback': ' | '.join([review.feedback[:100] + '...' for review in all_reviews])
            }
            
            def write_csv_file():
                with open(settings.ESCALATION_LOG_PATH, 'a', newline='', encoding='utf-8') as csvfile:
                    fieldnames = escalation_data.keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    # Write header if file is new
                    if not file_exists:
                        writer.writeheader()
                    
                    writer.writerow(escalation_data)
            
            # Execute file writing in a separate thread
            await asyncio.to_thread(write_csv_file)
        
        await write_to_csv()
        logger.info(f"Escalation logged for ticket {ticket.ticket_id}")
        
    except Exception as e:
        logger.error(f"Failed to log escalation: {e}")