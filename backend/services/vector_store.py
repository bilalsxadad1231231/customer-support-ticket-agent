# services/vector_store.py
import os
import pickle
import logging
from typing import List, Dict, Any, Optional

from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain.vectorstores import FAISS
from langchain.schema import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Assume settings are configured elsewhere, e.g., in a config file
# from config.settings import settings
class Settings:
    # Use absolute path for the embedding model
    EMBEDDING_MODEL= "sentence-transformers/all-MiniLM-L6-v2"
    CATEGORIES = ["general", "security", "billing", "technical"]
    INDEX_DIR = "index_storage"

settings = Settings()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class VectorStoreService:
    """
    A service for handling hybrid search (keyword + vector) over documents.
    It creates, saves, and loads retrievers for different categories.
    """
    def __init__(self):
        # Ensure the directory for storing index files exists
        os.makedirs(settings.INDEX_DIR, exist_ok=True)
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'}
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.ensemble_retrievers: Dict[str, EnsembleRetriever] = {}
        self._load_retrievers()

    def _load_retrievers(self):
        """Load pre-built retriever objects from disk for each category."""
        for category in settings.CATEGORIES:
            file_path = os.path.join(settings.INDEX_DIR, f"{category}_retriever.pkl")
            if os.path.exists(file_path):
                try:
                    with open(file_path, "rb") as f:
                        self.ensemble_retrievers[category] = pickle.load(f,)
                    logger.info(f"Successfully loaded retriever for category '{category}'.")
                except Exception as e:
                    logger.error(f"Failed to load retriever for '{category}': {e}")
            else:
                logger.warning(f"No pre-built retriever found for category '{category}'.")

    async def add_documents(self, documents: List[Document], category: str):
        """
        Processes and indexes documents for a specific category, creating a hybrid retriever.
        """
        if not documents:
            logger.warning(f"No documents provided for category '{category}'.")
            return
        logger.info(f"documents: {documents[0].page_content}")
        logger.info(f"Processing {len(documents)} documents for category '{category}'...")
        
        # 1. Split documents into manageable chunks
        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"Split documents into {len(chunks)} chunks.")

        if not chunks:
            logger.warning(f"\nNo chunks were created from documents for category '{category}'. The documents might be empty.")
            return

        # 2. Create a keyword-based retriever (BM25)
        bm25_retriever = BM25Retriever.from_documents(chunks)
        bm25_retriever.k = 5 # Number of results to fetch

        # 3. Create a vector-based retriever (FAISS)
        faiss_vectorstore = FAISS.from_documents(chunks, self.embeddings)
        faiss_retriever = faiss_vectorstore.as_retriever(search_kwargs={"k": 5})

        # 4. Create the hybrid ensemble retriever
        # We can adjust weights to prioritize one retriever over the other
        self.ensemble_retrievers[category] = EnsembleRetriever(
            retrievers=[bm25_retriever, faiss_retriever],
            weights=[0.5, 0.5] # 50% keyword-based, 50% vector-based
        )

        # 5. Save the created retriever to disk for future use
        file_path = os.path.join(settings.INDEX_DIR, f"{category}_retriever.pkl")
        with open(file_path, "wb") as f:
            pickle.dump(self.ensemble_retrievers[category], f)
            
        logger.info(f"Successfully created and saved hybrid retriever for category '{category}'.")

    async def search(self, query: str, category: str, k: int = 5) -> Dict[str, Any]:
        """
        Performs a hybrid search using the ensemble retriever for the given category.
        """
        if category not in self.ensemble_retrievers:
            return {
                'documents': [f"No knowledge base found for category '{category}'. Please build the index first."],
                'metadata': {
                    'error': 'Retriever not found.',
                    'category': category,
                    'query_used': query,
                    'num_results': 0
                }
            }

        try:
            retriever = self.ensemble_retrievers[category]
            # Note: EnsembleRetriever does not directly support 'k' parameter in get_relevant_documents.
            # The 'k' is set when creating the individual retrievers (bm25.k, faiss.as_retriever(k=...)).
            # The results are combined and duplicates are removed.
            results = retriever.get_relevant_documents(query)
            
            # The number of results might be less than k*2 due to deduplication.
            return {
                'documents': [doc.page_content for doc in results],
                'metadata': {
                    'category': category,
                    'query_used': query,
                    'num_results': len(results)
                }
            }
        except Exception as e:
            logger.error(f"Search error in category '{category}': {e}")
            return {
                'documents': [f"An error occurred during search for category '{category}'."],
                'metadata': {
                    'error': str(e),
                    'category': category,
                    'query_used': query,
                    'num_results': 0
                }
            }

    async def refine_search(self, original_query: str, category: str, feedback: str, k: int = 5) -> Dict[str, Any]:
        """
        Refines a search query based on feedback and performs a new search.
        """
        refined_query = f"{original_query} {feedback}"
        logger.info(f"Refining search for category '{category}' with new query: '{refined_query}'")
        return await self.search(query=refined_query, category=category, k=k)