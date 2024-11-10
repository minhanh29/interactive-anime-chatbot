from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core import Settings, Document
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance
from config import settings
from llm.factory import Factory
from typing import Optional
from pydantic import BaseModel
from time import time
import math
from datetime import datetime


class Information(BaseModel):
    importance: int
    timestamp: int
    time_str: str


class _SemanticSearch:
    def __init__(self):
        client = QdrantClient(host="localhost", port=6333)
        if not client.collection_exists(settings.SEARCH_INDEX):
            client.create_collection(
                collection_name=settings.SEARCH_INDEX,
                vectors_config=VectorParams(
                    size=384, distance=Distance.COSINE
                ),
                shard_number=6
            )

        vector_store = QdrantVectorStore(
            client=client,
            enable_hybrid=True,
            batch_size=32,
            collection_name=settings.SEARCH_INDEX
        )
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            service_context=Factory.service_context
        )
        self.retriever = self.index.as_retriever(
            similarity_top_k=50,
            sparse_top_k=100,
            vector_store_query_mode="hybrid"
        )
        print("Connected to QDrant")

    def insert(self, text: str, importance: int):
        self.index.insert(Document(
            text=text,
            metadata=Information(
                importance=importance,
                timestamp=int(time()),
                time_str=datetime.now().isoformat()
            )
        ))

    def query(self, text: str, k: int = 5):
        try:
            candidates = self.retriever.retrieve(text)
        except Exception as e:
            print("Qdrant error", e)
            return [], []

        relevances = []
        importances = []
        for item in candidates:
            text = item.get_text()
            metadata = item.metadata
            score = item.score * metadata["importance"]
            importances.append((text, score))

            time_decay = math.exp((metadata["timestamp"] - time()) / (3600 * 24))
            score *= time_decay
            time_str = datetime.fromisoformat(metadata["time_str"]).strftime("%d %B %Y")
            relevances.append((text, score, metadata["timestamp"], time_str))

        # sort by score
        relevances.sort(key=lambda x: x[1], reverse=True)
        relevances = [x for x in relevances]
        relevances = relevances[:min(k, len(relevances))]

        # sort by time
        relevances.sort(key=lambda x: x[2], reverse=True)
        relevance_set = set([x[0] for x in relevances])
        relevances = [f"{x[3]} - {x[0]}" for x in relevances]

        importances.sort(key=lambda x: x[1], reverse=True)
        importances = [x[0] for x in importances if x[0] not in relevance_set]
        importances = importances[:min(k, len(importances))]

        return relevances, importances


SemanticSearch: _SemanticSearch = _SemanticSearch()
# SemanticSearch = None
