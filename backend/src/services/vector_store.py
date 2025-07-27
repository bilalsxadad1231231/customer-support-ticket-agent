# services/vector_store.py
import os
import pickle
import logging
import asyncio
from typing import List, Dict, Any, Optional

from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain.vectorstores import FAISS
from langchain.schema import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.config.settings import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class VectorStoreService:
    """
    A service for handling hybrid search (keyword + vector) over documents.
    It creates, saves, and loads retrievers for different categories.
    """
    def __init__(self):
        # Ensure the directory for storing index files exists
        self._ensure_index_dir()
        
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

    async def _ensure_index_dir(self):
        """Ensure the index directory exists asynchronously"""
        await asyncio.to_thread(os.makedirs, settings.INDEX_DIR, exist_ok=True)

    async def _load_retrievers(self):
        """Load pre-built retriever objects from disk for each category asynchronously."""
        for category in settings.CATEGORIES:
            file_path = os.path.join(settings.INDEX_DIR, f"{category}_retriever.pkl")
            
            # Check if file exists asynchronously
            file_exists = await asyncio.to_thread(os.path.exists, file_path)
            
            if file_exists:
                try:
                    # Load retriever asynchronously
                    def load_retriever():
                        with open(file_path, "rb") as f:
                            return pickle.load(f)
                    
                    self.ensemble_retrievers[category] = await asyncio.to_thread(load_retriever)
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

        # 5. Save the created retriever to disk for future use asynchronously
        file_path = os.path.join(settings.INDEX_DIR, f"{category}_retriever.pkl")
        
        def save_retriever():
            with open(file_path, "wb") as f:
                pickle.dump(self.ensemble_retrievers[category], f)
        
        await asyncio.to_thread(save_retriever)
            
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




    async def refine_search(
        self, 
        queries: List[str], 
        category: str, 
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Simple refined search using multiple queries with deduplication.
        
        Args:
            queries: List of refined search queries to use
            category: Document category to search in
            k: Number of final documents to return
            
        Returns:
            Dictionary with combined search results from all queries
        """
        
        if not queries:
            logger.warning("No queries provided for refined search")
            return {
                'documents': [],
                'metadata': {
                    'category': category,
                    'query_used': 'No queries provided'
                }
            }
        
        try:
            logger.info(f"Performing refined search with {len(queries)} queries for category '{category}'")
            
            # Search with each refined query and collect all documents
            all_documents = []
            
            for i, query in enumerate(queries):
                try:
                    logger.debug(f"Searching with query {i+1}: '{query}'")
                    
                    result = await self.search(query=query, category=category, k=k)
                    
                    if result.get('documents'):
                        all_documents.extend(result['documents'])
                        logger.debug(f"Query '{query}' returned {len(result['documents'])} documents")
                    else:
                        logger.warning(f"Query '{query}' returned no documents")
                        
                except Exception as e:
                    logger.error(f"Error searching with query '{query}': {e}")
                    continue
            
            if not all_documents:
                logger.warning("No documents found with any refined query")
                return {
                    'documents': [],
                    'metadata': {
                        'category': category,
                        'queries_used': queries,
                        'query_used': f"Multi-query search with {len(queries)} queries (no results)"
                    }
                }
            
            # Simple deduplication - remove duplicate documents
            unique_documents = self._remove_duplicates(all_documents)
            
            # Return top k documents
            final_documents = unique_documents[:10]
            
            logger.info(f"Refined search completed: {len(final_documents)} unique documents from {len(all_documents)} total results")
            
            return {
                'documents': final_documents,
                'metadata': {
                    'category': category,
                    'queries_used': queries,
                    'total_documents_found': len(all_documents),
                    'unique_documents_returned': len(final_documents),
                    'query_used': f"Multi-query search using {len(queries)} queries"
                }
            }
            
        except Exception as e:
            logger.error(f"Multi-query search failed: {e}")
            return {
                'documents': [],
                'metadata': {
                    'category': category,
                    'queries_used': queries,
                    'error': str(e),
                    'query_used': f"Failed multi-query search with {len(queries)} queries"
                }
            }

    def _remove_duplicates(self, documents: List[str]) -> List[str]:
        """
        Simple deduplication based on document content similarity.
        
        Args:
            documents: List of document strings
            
        Returns:
            List of unique documents
        """
        
        unique_docs = []
        seen_signatures = set()
        
        for doc in documents:
            # Use first 100 characters as document signature for deduplication
            signature = doc[:100].lower().strip()
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_docs.append(doc)
        
        return unique_docs
