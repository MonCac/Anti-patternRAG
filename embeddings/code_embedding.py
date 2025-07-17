from typing import List
from langchain_ollama import OllamaEmbeddings
from config.settings import LLM_MODEL

model = LLM_MODEL


def get_embedding_model():
    # 简单封装，后续可改成 CodeBERT/CodeT5 等模型
    embed = OllamaEmbeddings(
        model=model
    )
    return embed


# 只适配 ollama 的单文本 string 嵌入
def embed_chunk(embed_model, chunk: str) -> List[float]:
    embedding = embed_model.embed_query(chunk)
    return embedding
