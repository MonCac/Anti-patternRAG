from pathlib import Path
from typing import Union
from transformers import AutoTokenizer

from config.settings import TEXT_EMBEDDING_MODEL
from embeddings.EmbeddingWrapper import QwenEmbeddingWrapper
from embeddings.embedding_utils import (
    load_chunks_from_json,
    build_documents,
    init_embedding_model,
    store_to_chroma, get_max_token_length,
    check_documents_exceed_max_len, get_query_vectorstore_dir
)
from splitter.utils import split_documents_with_instruction_context


def build_text_embedding(chunks_json_path: Union[str, Path], query: bool = False):
    chunks = load_chunks_from_json(Path(chunks_json_path))
    documents = build_documents(chunks, content_key="llm_description")
    embedding_model_raw = init_embedding_model(TEXT_EMBEDDING_MODEL)
    embedding_model = QwenEmbeddingWrapper(embedding_model_raw)
    tokenizer = AutoTokenizer.from_pretrained(TEXT_EMBEDDING_MODEL, trust_remote_code=True)
    model_max_len = get_max_token_length(tokenizer)
    match TEXT_EMBEDDING_MODEL:
        case m if "Qwen/Qwen3-Embedding-8B" in m:
            valid_documents, exceeding_documents = check_documents_exceed_max_len(documents, tokenizer, model_max_len)
            if len(exceeding_documents) > 0:
                exceeding_documents = split_documents_with_instruction_context(exceeding_documents, tokenizer,
                                                                               model_max_len)
            documents = valid_documents + exceeding_documents
        case _:
            pass

    try:
        store_to_chroma(documents, embedding_model, "TEXT", query=query)
    except Exception as e:
        print(f"[Error] build_text_embedding failed: {e}", flush=True)
        raise
    print("[✓] finish text_code_embedding", flush=True)

    return
