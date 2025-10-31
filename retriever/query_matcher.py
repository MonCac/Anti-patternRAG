from config.settings import ANTIPATTERN_TYPE
from embeddings.runner import run_embedding_pipeline
from splitter.strategy_registry import load_splitter_by_mode

antipattern_type = ANTIPATTERN_TYPE


# 完成 query 的 chunk 分块
def load_query_chunks(case_path: str, antipattern_type: str, mode="ast"):
    print("enter load_query_chunks")
    group_id = -1
    build_chunks = load_splitter_by_mode(mode)
    print("enter build_chunks = load_splitter_by_mode(mode)")
    print(f"build_chunks : {build_chunks}")
    chunks, query_chunk_path = build_chunks(case_path, antipattern_type, group_id)
    return chunks, query_chunk_path


# 完成 query 的 chunks 的 embedding
def load_query_embeddings(chunk_path: str, query: bool):
    query_embedding_path = run_embedding_pipeline(chunk_path, query)
    return query_embedding_path
