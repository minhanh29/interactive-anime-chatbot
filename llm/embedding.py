from llama_index.embeddings.openai.base import BaseEmbedding
from typing import List
import boto3
import json
from llama_index.core.bridge.pydantic import PrivateAttr


class TitanEmbedding(BaseEmbedding):
    _bedrock_client: object = PrivateAttr()

    def __init__(self):
        self._bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name="ap-northeast-1",
        )
        super().__init__()

    @classmethod
    def class_name(cls) -> str:
        return "TitanEmbedding"

    def _embed(self, sentences: List[str]) -> List[List[float]]:
        """Embed sentences."""
        embeddings = []
        for text in sentences:
            response = self._bedrock_client.invoke_model(
                        body=json.dumps({"inputText": text}),
                        modelId='amazon.titan-embed-text-v1',
                        accept='application/json',
                        contentType='application/json'
            )
            result = json.loads(response['body'].read())
            embedding = result.get('embedding')
            embeddings.append(embedding)
        return embeddings

    def _get_query_embedding(self, query: str) -> List[float]:
        """Get query embedding."""
        return self._embed([query])[0]

    async def _aget_query_embedding(self, query: str) -> List[float]:
        """Get query embedding async."""
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        """Get text embedding async."""
        return self._get_text_embedding(text)

    def _get_text_embedding(self, text: str) -> List[float]:
        """Get text embedding."""
        return self._embed([text])[0]

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get text embeddings."""
        return self._embed(texts)
