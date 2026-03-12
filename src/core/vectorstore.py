import logging
import os
from datetime import datetime
from typing import List, Any, Dict, Union, Optional
from src.api.setup_api import logger
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document

# -----------------------------
# Vector Store Handler
# -----------------------------
class VectorStore:
    """Manages Pinecone vector store operations"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.store = None
        self.embeddings = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Pinecone connection and embeddings"""
        try:
            # Initialize Pinecone
            pc = Pinecone(api_key=self.config['PINECONE_API_KEY'])
            index_name = self.config['PINECONE_INDEX']
            
            # ✅ Initialize embeddings first (before index creation)
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.config['EMBED_MODEL'],
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True},
                cache_folder='./models'
            )

            # ✅ Get embedding dimension before using it
            dimension = int(self.config.get("EMBED_DIMENSION", len(self.embeddings.embed_query("test"))))
            logger.info(f"Using embedding dimension: {dimension}")

            # Check if index exists
            existing_indexes = [idx.name for idx in pc.list_indexes()]

            # If an existing index has the wrong dimension, switch to a dimension-specific index.
            if index_name in existing_indexes:
                try:
                    index_info = pc.describe_index(index_name)
                    existing_dimension = getattr(index_info, "dimension", None)
                    if existing_dimension is None and isinstance(index_info, dict):
                        existing_dimension = index_info.get("dimension")
                except Exception as describe_error:
                    logger.warning(f"Could not read dimension for index '{index_name}': {describe_error}")
                    existing_dimension = None

                if existing_dimension is not None and int(existing_dimension) != dimension:
                    compatible_index_name = f"{index_name}-{dimension}"
                    logger.warning(
                        "Index '%s' has dimension %s but embeddings are %s. Using '%s' instead.",
                        index_name,
                        existing_dimension,
                        dimension,
                        compatible_index_name,
                    )
                    index_name = compatible_index_name
                    self.config['PINECONE_INDEX'] = index_name
                    existing_indexes = [idx.name for idx in pc.list_indexes()]

            if index_name not in existing_indexes:
                logger.info(f"Index '{index_name}' not found. Creating it...")
                
                try:
                    # Create index with appropriate spec based on plan
                    from pinecone import ServerlessSpec, PodSpec
                    
                    # Try serverless first (more cost-effective)
                    try:
                        pc.create_index(
                            name=index_name,
                            dimension=dimension,
                            metric='cosine',
                            spec=ServerlessSpec(cloud='aws', region='us-east-1')
                        )
                        logger.info(f"Created serverless index '{index_name}'")
                    except Exception as serverless_error:
                        logger.warning(f"Serverless creation failed: {serverless_error}")
                        logger.info("Trying pod-based index...")
                        
                        # Fallback to pod-based
                        pc.create_index(
                            name=index_name,
                            dimension=dimension,
                            metric='cosine',
                            spec=PodSpec(environment='gcp-starter', pod_type='s1.x1')
                        )
                        logger.info(f"Created pod-based index '{index_name}'")
                    
                    # Wait for index to be ready
                    import time
                    logger.info("Waiting for index to be ready...")
                    time.sleep(10)  # Give it some time to initialize
                    
                except Exception as create_error:
                    error_msg = (
                        f"Failed to create Pinecone index '{index_name}': {create_error}\n"
                        f"Please manually create it in the Pinecone console with: "
                        f"dimension={dimension}, metric=cosine"
                    )
                    logger.error(error_msg)
                    raise ValueError(error_msg)
            
            index = pc.Index(index_name)
            
            # Initialize embeddings
            # self.embeddings = HuggingFaceEmbeddings(
            #     model_name=self.config['EMBED_MODEL'],
            #     model_kwargs={'device': 'cpu'},
            #     encode_kwargs={'normalize_embeddings': True},
            #     cache_folder='./models'
            # )

            # Initialize vector store
            self.store = PineconeVectorStore(
                index=index, 
                embedding=self.embeddings, 
                text_key='text'
            )
            
            logger.info(f"Vector store initialized with index: {index_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def add_documents(self, texts: List[str], session_id: str) -> int:
        """Add document chunks to vector store"""
        if not texts:
            return 0
        
        try:
            # Create documents with metadata
            documents = []
            for i, text in enumerate(texts):
                doc = Document(
                    page_content=text,
                    metadata={
                        'session_id': session_id,
                        'chunk_id': f"{session_id}_{i}",
                        'timestamp': datetime.now().isoformat()
                    }
                )
                documents.append(doc)
            
            # Add to vector store
            ids = self.store.add_documents(documents)
            logger.info(f"Added {len(documents)} documents to vector store")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {e}")
            raise
    
    def get_retriever(self, session_id: str, k: int = 5):
        """Get retriever for specific session"""
        try:
            if not self.store:
                logger.warning("Vector store not initialized, creating dummy retriever")
                # Return a dummy retriever that returns empty results
                from langchain.schema import BaseRetriever, Document
                
                class DummyRetriever(BaseRetriever):
                    def get_relevant_documents(self, query: str):
                        return []
                    
                    async def aget_relevant_documents(self, query: str):
                        return []
                
                return DummyRetriever()
            
            # Create retriever with session filter
            retriever = self.store.as_retriever(
                search_kwargs={
                    'k': k,
                    'filter': {'session_id': session_id}
                }
            )
            
            return retriever
            
        except Exception as e:
            logger.error(f"Failed to create retriever: {e}")
            # Return a dummy retriever as fallback
            from langchain.schema import BaseRetriever, Document
            
            class DummyRetriever(BaseRetriever):
                def get_relevant_documents(self, query: str):
                    return []
                
                async def aget_relevant_documents(self, query: str):
                    return []
            
            return DummyRetriever()
