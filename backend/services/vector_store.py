# services/vector_store.py
import os
import pickle
import logging
from typing import List, Dict, Any, Optional
import faiss
import numpy as np
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import DirectoryLoader, TextLoader
from config.settings import settings

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'}
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.vector_stores = {}
        self.document_metadata = {}
        
    async def initialize_vector_stores(self):
        """Initialize vector stores for each category"""
        for category in settings.CATEGORIES:
            await self._build_category_vector_store(category)
    
    async def _build_category_vector_store(self, category: str):
        """Build vector store for a specific category"""
        try:
            knowledge_path = settings.KNOWLEDGE_BASE_PATHS[category]
            
            if not os.path.exists(knowledge_path):
                logger.warning(f"Knowledge base path not found: {knowledge_path}")
                self._create_sample_documents(category, knowledge_path)
            
            # Load documents
            loader = DirectoryLoader(
                knowledge_path,
                glob="*.txt",
                loader_cls=TextLoader
            )
            documents = loader.load()
            
            if not documents:
                logger.warning(f"No documents found for category: {category}")
                self._create_sample_documents(category, knowledge_path)
                documents = loader.load()
            
            # Split documents
            chunks = self.text_splitter.split_documents(documents)
            
            # Create embeddings
            texts = [chunk.page_content for chunk in chunks]
            embeddings_array = np.array(self.embeddings.embed_documents(texts))
            
            # Create FAISS index
            dimension = embeddings_array.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings_array.astype('float32'))
            
            # Store
            self.vector_stores[category] = index
            self.document_metadata[category] = {
                'texts': texts,
                'metadata': [chunk.metadata for chunk in chunks]
            }
            
            logger.info(f"Built vector store for {category}: {len(texts)} chunks")
            
        except Exception as e:
            logger.error(f"Error building vector store for {category}: {e}")
            self._create_fallback_vector_store(category)
    
    def _create_sample_documents(self, category: str, path: str):
        """Create sample documents if none exist"""
        os.makedirs(path, exist_ok=True)
        
        sample_docs = {
            "billing": [
                "Billing FAQ: Our billing cycle runs monthly. Charges appear 1-2 business days after your billing date.",
                "Refund Policy: Refunds are processed within 5-7 business days for eligible cancellations.",
                "Payment Issues: If your payment fails, please update your payment method in account settings."
            ],
            "technical": [
                "API Documentation: Use authentication headers for all API requests. Rate limits apply.",
                "Common Issues: Login problems are often resolved by clearing browser cache and cookies.",
                "System Status: Check our status page for current system availability and known issues."
            ],
            "security": [
                "Security Guidelines: Enable two-factor authentication for enhanced account security.",
                "Privacy Policy: We protect your data with industry-standard encryption and security measures.",
                "Suspicious Activity: Report any suspicious account activity immediately to our security team."
            ],
            "general": [
                "Company Information: We provide customer support 24/7 via chat, email, and phone.",
                "Getting Started: New users should complete account setup and explore our tutorial resources.",
                "Feedback: We welcome your feedback and suggestions for improving our service."
            ]
        }
        
        for i, content in enumerate(sample_docs.get(category, [])):
            with open(f"{path}/doc_{i+1}.txt", "w") as f:
                f.write(content)
    
    def _create_fallback_vector_store(self, category: str):
        """Create a minimal fallback vector store"""
        fallback_text = f"General information for {category} category. Please contact support for specific assistance."
        embedding = np.array(self.embeddings.embed_documents([fallback_text]))
        
        dimension = embedding.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embedding.astype('float32'))
        
        self.vector_stores[category] = index
        self.document_metadata[category] = {
            'texts': [fallback_text],
            'metadata': [{'source': 'fallback', 'category': category}]
        }
    
    async def search(
        self, 
        query: str, 
        category: str, 
        k: int = 5,
        refined_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search for relevant documents"""
        try:
            if category not in self.vector_stores:
                await self._build_category_vector_store(category)
            
            search_query = refined_query if refined_query else query
            query_embedding = np.array(self.embeddings.embed_query(search_query))
            
            # Search in FAISS index
            index = self.vector_stores[category]
            distances, indices = index.search(query_embedding.reshape(1, -1).astype('float32'), k)
            
            # Get relevant documents
            metadata = self.document_metadata[category]
            documents = []
            
            for idx in indices[0]:
                if idx < len(metadata['texts']):
                    documents.append(metadata['texts'][idx])
            
            return {
                'documents': documents,
                'metadata': {
                    'category': category,
                    'query_used': search_query,
                    'num_results': len(documents),
                    'distances': distances[0].tolist()
                },
                'query_used': search_query
            }
            
        except Exception as e:
            logger.error(f"Search error for category {category}: {e}")
            return {
                'documents': [f"Error retrieving information for {category}. Please contact support."],
                'metadata': {'category': category, 'error': str(e)},
                'query_used': query
            }
    
    async def refine_search(
        self, 
        original_query: str, 
        category: str, 
        feedback: str,
        k: int = 5
    ) -> Dict[str, Any]:
        """Refine search based on reviewer feedback"""
        # Create refined query based on feedback
        refined_query = f"{original_query} {feedback}"
        
        return await self.search(
            query=original_query,
            category=category,
            k=k,
            refined_query=refined_query
        )