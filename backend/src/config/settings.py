# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Model Configuration
    GROQ_MODEL = "llama3-70b-8192"
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Graph Configuration
    MAX_RETRIES = 2
    VECTOR_STORE_PATH = "data/vector_store"
    ESCALATION_LOG_PATH = "data/escalation_log.csv"
    
    # Categories
    CATEGORIES = ["billing", "technical", "security", "general"]
    
    # Knowledge Base Paths
    KNOWLEDGE_BASE_PATHS = {
        "billing": "data/knowledge_base/billing",
        "technical": "data/knowledge_base/technical", 
        "security": "data/knowledge_base/security",
        "general": "data/knowledge_base/general"
    }

    # Vector Store Configuration
    INDEX_DIR = "index_storage"

settings = Settings()