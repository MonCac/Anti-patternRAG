import json
from pathlib import Path
from typing import List, Union
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

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


def init_embedding_model(model_name: str, device: str = "cpu", normalize: bool = False, default_task: str = None):
    model_kwargs = {"device": device, "trust_remote_code": True}
    if default_task is not None:
        model_kwargs["default_task"] = default_task
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs={"normalize_embeddings": normalize},
    )


def store_to_chroma(documents: List[Document], embedding_model, persist_dir):
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        persist_directory=persist_dir,
    )
    vectorstore.persist()
    print(f"[✓] Stored {len(documents)} documents to Chroma: {persist_dir}")
    return vectorstore


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
