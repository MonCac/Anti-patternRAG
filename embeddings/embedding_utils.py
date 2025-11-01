import json
import os
import pickle
from pathlib import Path
from typing import List, Union

import numpy as np
from langchain.schema import Document
import faiss
from langchain_huggingface import HuggingFaceEmbeddings
from tqdm import tqdm
from prompts.prompt_loader import load_prompt

PROMPT_FILE_MAP = {
    "parent_file_summary": "parent_file_summary.txt",
    "parent_method_summary": "parent_method_summary.txt",
    "invocation_summary": "invocation_summary.txt",
    "child_file_summary": "child_file_summary.txt",
    "child_method_summary": "child_method_summary.txt",
}


def load_chunks_from_json(json_path: Path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def build_documents(chunks_json: dict, content_key: str) -> List[Document]:
    """
    构建 Document 列表：
    - page_content 来源于每个 chunk 的 content_key 字段（如 ast_subtree / llm_description）
    - metadata 合并 chunk 字段和顶层元信息（antipattern_type, project_name 等）

    :param chunks_json: load 后的整个 JSON 内容（包含顶层元数据和 chunks）
    :param content_key: 使用哪个字段作为向量内容，如 "ast_subtree" 或 "llm_description"
    """
    all_documents = []
    case_metadata = {k: v for k, v in chunks_json.items() if k != "chunks"}
    chunks = chunks_json["chunks"]

    for chunk in chunks:
        if content_key not in chunk:
            continue

        content = chunk[content_key]
        chunk_metadata = {k: v for k, v in chunk.items() if k != content_key}
        full_metadata = {**case_metadata, **chunk_metadata}

        all_documents.append(Document(page_content=content, metadata=full_metadata))

    return all_documents


def init_embedding_model(model_name: str, device: str = "cpu", normalize: bool = False):
    model_kwargs = {"device": device, "trust_remote_code": True}
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs={"normalize_embeddings": normalize},
    )


def store_to_chroma(documents: List[Document], embedding_model,
                    type: str,
                    base_path: str = "vectorstore",
                    batch_size: int = 2,
                    query: bool = False):
    """
    Stores documents into a native FAISS index with batch embedding and metadata support.

    Args:
        documents: List of Document objects.
        embedding_model: Object with embed_documents([text]) -> list[float].
        batch_size: Number of documents processed per batch.

    Returns:
        index: FAISS index object.
        metadatas: List of metadata dictionaries corresponding to documents.
        :param documents:
        :param type:
        :param base_path:
    """
    if not documents:
        print("[i] No documents to store.")
        return None, None

    # === 路径逻辑修改区 ===
    if query:
        # 固定路径结构: query/vectorstore/CODE 或 TEXT
        folder_path = os.path.join("query", "vectorstore", type)
    else:
        # 原有逻辑: 根据 metadata 创建层级路径
        first_meta = documents[0].metadata
        folder_path = os.path.join(
            base_path,
            type,
            first_meta["antipattern_type"],
            first_meta["project_name"],
            first_meta["commit_number"],
            str(first_meta["id"])
        )
    os.makedirs(folder_path, exist_ok=True)
    index_path = os.path.join(folder_path, "faiss_index.idx")
    metadata_path = os.path.join(folder_path, "metadata.pkl")

    print(f"[i] Generating embeddings for {len(documents)} documents...")

    # 生成 embeddings 并保存在 metadata
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i + batch_size]
        batch_texts = [doc.page_content for doc in batch_docs]

        for j, text in enumerate(tqdm(batch_texts,
                                      desc=f"Embedding batch {i // batch_size + 1}/{(len(documents) + batch_size - 1) // batch_size}",
                                      leave=False)):
            if query:
                # embed_query 对单个字符串，返回 list[float]
                emb = embedding_model.embed_query(text)
            else:
                # embed_documents 要传入列表，返回 List[List[float]]
                emb = embedding_model.embed_documents([text])[0]
            batch_docs[j].metadata["embedding"] = np.array(emb, dtype=np.float32)

    # 构建 FAISS 索引
    dim = len(documents[0].metadata["embedding"])
    index = faiss.IndexFlatL2(dim)
    embeddings = np.array([doc.metadata["embedding"] for doc in documents], dtype=np.float32)

    # 批量插入 FAISS
    print("[i] Adding embeddings to FAISS index...")
    for i in tqdm(range(0, len(embeddings), batch_size), desc="Inserting batches", unit="batch"):
        batch_embeddings = embeddings[i:i + batch_size]
        index.add(batch_embeddings)

    # 保存 FAISS 索引
    faiss.write_index(index, index_path)
    print(f"[✓] FAISS index saved to {index_path}")

    # 保存 metadata
    metadatas = [doc.metadata for doc in documents]
    with open(metadata_path, "wb") as f:
        pickle.dump(metadatas, f)
    print(f"[✓] Metadata saved to {metadata_path}")

    return os.path.dirname(folder_path)


def get_persist_dir_from_chunk_path(vector_store_dir: str, chunk_json_path: Path) -> str:
    # 解析倒数四级路径部分
    parts = chunk_json_path.parts[-5:-1]
    persist_dir = Path(vector_store_dir).joinpath(*parts)
    return str(persist_dir)


def get_query_vectorstore_dir(chunks_json_path: str | Path, vectorstore_type: str) -> Path:
    """
    在 chunks_json_path 所在目录下，创建 vectorstore/{vectorstore_type}/ 子目录。

    :param chunks_json_path: JSON 文件路径（str 或 Path）
    :param vectorstore_type: 子目录名（"CODE", "TEXT"）
    :return: 拼接后的向量数据库目录 Path
    """
    chunks_path = Path(chunks_json_path)
    persist_dir = chunks_path.parent / "vectorstore" / vectorstore_type
    persist_dir.mkdir(parents=True, exist_ok=True)
    return persist_dir


def add_prompts_to_documents_qwen3(documents: List[Document], prompt_dir: Union[Path, str]) -> List[Document]:
    new_documents = []

    for doc in documents:
        chunk_type = doc.metadata.get("chunk_type", "")
        prompt_key = f"{prompt_dir}/{chunk_type}"
        prompt = load_prompt(prompt_key)
        new_content = f"{prompt}\nQuery: {doc.page_content}"
        new_documents.append(Document(page_content=new_content, metadata=doc.metadata))

    return new_documents


def get_max_token_length(tokenizer) -> int:
    max_len = tokenizer.model_max_length
    if max_len > 100000:
        max_len = 32768  # 默认上限兜底
    return max_len


def check_documents_exceed_max_len(documents: List[Document], tokenizer, model_max_len: int):
    """
    检查哪些 documents 的 page_content 超过模型最大 token 长度。

    :param documents: 要分析的 Document 列表
    :param tokenizer: 已加载的 tokenizer（AutoTokenizer）
    :param model_max_len: 模型支持的最大 token 数
    :return: (valid_documents, exceeding_documents) 元组
    """
    valid_documents = []
    exceeding_documents = []

    for doc in documents:
        token_count = len(tokenizer.encode(doc.page_content, truncation=False))
        if token_count <= model_max_len:
            valid_documents.append(doc)
        else:
            exceeding_documents.append(doc)

    return valid_documents, exceeding_documents
