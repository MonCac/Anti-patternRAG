from pathlib import Path
from typing import Union

from transformers import AutoTokenizer

from config.settings import CODE_EMBEDDING_MODEL
from embeddings.EmbeddingWrapper import JinaCodeEmbeddingWrapper
from embeddings.embedding_utils import (
    load_chunks_from_json,
    build_documents,
    init_embedding_model,
    store_to_chroma,
    get_max_token_length, check_documents_exceed_max_len, get_query_vectorstore_dir,
)
from splitter.utils import split_ast_documents


def build_code_embedding(chunks_json_path: Union[str, Path], vectorstore_base_path, query: bool = False):
    chunks = load_chunks_from_json(Path(chunks_json_path))
    documents = build_documents(chunks, content_key="ast_subtree")
    embedding_model_raw = init_embedding_model(CODE_EMBEDDING_MODEL)
    embedding_model = JinaCodeEmbeddingWrapper(embedding_model_raw)
    tokenizer = AutoTokenizer.from_pretrained(CODE_EMBEDDING_MODEL, trust_remote_code=True)
    model_max_len = get_max_token_length(tokenizer)
    match CODE_EMBEDDING_MODEL:
        case m if "jinaai/jina-embeddings-v4" in m:
            valid_documents, exceeding_documents = check_documents_exceed_max_len(documents, tokenizer, model_max_len)
            if len(exceeding_documents) > 0:
                print(f"have exceeding_documents,len: {exceeding_documents}")
                exceeding_documents = split_ast_documents(exceeding_documents, tokenizer,model_max_len)
            else:
                print("donot have exceeding_documents")
            documents = valid_documents + exceeding_documents
        case _:
            pass
    try:
        path = store_to_chroma(documents, embedding_model, "CODE", vectorstore_base_path=vectorstore_base_path, query=query)
    except Exception as e:
        print(f"[Error] build_code_embedding failed: {e}", flush=True)
        raise
    print("[✓] finish build_code_embedding", flush=True)
    return path
