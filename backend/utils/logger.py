# utils/logger.py
import os
import csv
import logging
import asyncio
from datetime import datetime
from typing import List, Optional
from workflow.state import SupportTicket, ClassificationResult, DraftResponse, ReviewResult
from config.settings import settings

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
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(settings.ESCALATION_LOG_PATH), exist_ok=True)
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(settings.ESCALATION_LOG_PATH)
        
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
        
        # Write to CSV
        with open(settings.ESCALATION_LOG_PATH, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = escalation_data.keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header if file is new
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(escalation_data)
        
        logger.info(f"Escalation logged for ticket {ticket.ticket_id}")
        
    except Exception as e:
        logger.error(f"Failed to log escalation: {e}")

# utils/validators.py
from typing import Dict, Any, List
import re

class TicketValidator:
    """Validator for support tickets"""
    
    @staticmethod
    def validate_ticket_input(subject: str, description: str) -> Dict[str, Any]:
        """Validate ticket input parameters"""
        
        errors = []
        
        # Subject validation
        if not subject or not subject.strip():
            errors.append("Subject is required")
        elif len(subject.strip()) < 5:
            errors.append("Subject must be at least 5 characters")
        elif len(subject.strip()) > 200:
            errors.append("Subject must be less than 200 characters")
        
        # Description validation  
        if not description or not description.strip():
            errors.append("Description is required")
        elif len(description.strip()) < 10:
            errors.append("Description must be at least 10 characters")
        elif len(description.strip()) > 5000:
            errors.append("Description must be less than 5000 characters")
        
        # Check for suspicious content
        suspicious_patterns = [
            r'<script.*?>.*?</script>',  # Script tags
            r'javascript:',              # JavaScript URLs
            r'on\w+\s*=',               # Event handlers
        ]
        
        full_text = f"{subject} {description}".lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                errors.append("Suspicious content detected")
                break
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "cleaned_subject": subject.strip() if subject else "",
            "cleaned_description": description.strip() if description else ""
        }
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize text input"""
        if not text:
            return ""
        
        # Remove potentially harmful content
        text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

class ResponseValidator:
    """Validator for response quality"""
    
    @staticmethod
    def validate_response_quality(response: str) -> Dict[str, Any]:
        """Validate response quality metrics"""
        
        if not response or not response.strip():
            return {
                "valid": False,
                "score": 0.0,
                "issues": ["Empty response"]
            }
        
        issues = []
        score = 1.0
        
        # Length checks
        if len(response.strip()) < 20:
            issues.append("Response too short")
            score -= 0.3
        elif len(response.strip()) > 2000:
            issues.append("Response too long")
            score -= 0.1
        
        # Professional tone checks
        unprofessional_words = ['stupid', 'dumb', 'idiot', 'ridiculous']
        if any(word in response.lower() for word in unprofessional_words):
            issues.append("Unprofessional language detected")
            score -= 0.4
        
        # Helpful content checks
        helpful_indicators = ['help', 'assist', 'support', 'resolve', 'solution']
        if not any(word in response.lower() for word in helpful_indicators):
            issues.append("Response may not be helpful")
            score -= 0.2
        
        # Completeness check
        if response.strip().endswith('...') or 'incomplete' in response.lower():
            issues.append("Response appears incomplete")
            score -= 0.3
        
        return {
            "valid": score >= 0.6,
            "score": max(0.0, score),
            "issues": issues
        }