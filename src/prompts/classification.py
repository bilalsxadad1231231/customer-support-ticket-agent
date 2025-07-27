# prompts/classification.py

CLASSIFICATION_PROMPT = """
You are a support ticket classifier. Analyze the following support ticket and classify it into one of these categories:

Categories:
- billing: Payment issues, subscription problems, refunds, pricing questions
- technical: Bug reports, feature requests, API issues, system problems
- security: Account security, data privacy, suspicious activity, access issues
- general: General inquiries, company information, feedback, other

Ticket:
Subject: {subject}
Description: {description}

Provide your classification in this exact JSON format:
{{
    "category": "one of: billing, technical, security, general",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of why you chose this category"
}}

Be decisive and choose the most appropriate category even if the ticket could fit multiple categories.
"""



# prompts/review.py
