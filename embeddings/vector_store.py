from typing import List

import chromadb
from chromadb.api.models.Collection import Collection


def save_embeddings(chunks: List[str], embeddings: List[List[float]]) -> Collection:
    chromadb_client = chromadb.PersistentClient("./chromadb")
    chromadb_collection = chromadb_client.get_or_create_collection(name="default")
    ids = [str(i) for i in range(len(chunks))]
    chromadb_collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids
    )
    return chromadb_collection
