from pathlib import Path

from config.settings import DATA_DIR, CHUNKS_DATA_DIR
from embeddings.runner import run_embedding_pipeline, embedding_all_chunks
# from pipeline.rag_chain import build_basic_rag_chain
from prompts.prompt_loader import load_prompt
from retriever.runner import run_query_matching_pipeline
from splitter.ch_ast_splitter.ast_case_splitter import build_chunks
from splitter.runner import chunk_all_cases

# def main():
#     print("[RAG Demo] 输入 exit 退出")
#     while True:
#         sum = 4
#         question = load_prompt("example").format(sum=sum)
#         query = input(question)
#         if query.lower() in ("exit", "quit"):
#             break
#         result = build_basic_rag_chain(query)
#         print("\n===== RAG回答 =====")
#         print(result)


if __name__ == "__main__":
    # main()
    # chunk_all_cases(Path(DATA_DIR), "CH")
    # embedding_all_chunks(Path(CHUNKS_DATA_DIR))
    run_query_matching_pipeline("default", "/data/sanglei/Anti-patternRAG/query", 5)
    # run_embedding_pipeline("/data/sanglei/Anti-patternRAG/data/CH/kafka/commit_1000/6/kafka_6_CH_chunk.json")
    # run_embedding_pipeline("/data/sanglei/Anti-patternRAG/data/CH/kafka/commit_1000/6/kafka_6_CH_chunk.json")
