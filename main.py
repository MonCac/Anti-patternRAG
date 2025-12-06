import json
import os
from glob import glob
from pathlib import Path

from config.settings import DATA_DIR, CHUNKS_DATA_DIR, CH_CHUNK_TYPE_WEIGHT_PATH, VECTORSTORE_DATA_DIR
from embeddings.runner import run_embedding_pipeline, embedding_all_chunks
# from pipeline.rag_chain import build_basic_rag_chain
from prompts.prompt_loader import load_prompt
from retriever.init_vectprstpre import match_merged_chunks_faiss
from retriever.runner import run_query_matching_pipeline, batch_process_query, batch_process_vectorstore_query
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
    vectorstore_path = "/Users/moncheri/Downloads/main/重构/反模式修复数据集构建/RefactorRAG/Anti-PatternRAG/tmp/vectorstore"
    base_dir = "/Users/moncheri/Downloads/main/重构/反模式修复数据集构建/RefactorRAG/Anti-PatternRAG/tmp/merged_match_scores"
    # main()
    # 进行 CH chunk
    # chunk_all_cases(Path(DATA_DIR), "CH")
    # 对 chunk 的结果进行 embedding
    # embedding_all_chunks(Path(CHUNKS_DATA_DIR), "CH")
    # 直接对向量数据库的内容按照 CODE 和 TEXT 进行自评分
    # batch_process_vectorstore_query(vectorstore_path)
    # 对query 进行 chunk、embedding，并且进行最后的层级评分排序得到结果。
    # 结果存储在 query/vectorstore/aggregated_result.json
    # run_query_matching_pipeline("/data/sanglei/Anti-patternRAG/vectorstore", "/data/sanglei/Anti-patternRAG/query", 5)
    # run_embedding_pipeline("/data/sanglei/Anti-patternRAG/data/CH/kafka/commit_1000/6/kafka_6_CH_chunk.json")
    # run_embedding_pipeline("/data/sanglei/Anti-patternRAG/data/CH/kafka/commit_1000/6/kafka_6_CH_chunk.json")

    # 进行 MH chunk
    # chunk_all_cases(Path(DATA_DIR), "MH")
    # 对 chunk 的结果进行 embedding
    # embedding_all_chunks(Path(CHUNKS_DATA_DIR), VECTORSTORE_DATA_DIR, "MH")
    # 直接对向量数据库的内容按照 CODE 和 TEXT 进行自评分
    # batch_process_vectorstore_query(vectorstore_path, "MH")
    # 对query 进行 chunk、embedding，并且进行最后的层级评分排序得到结果。
    # 结果存储在 query/vectorstore/aggregated_result.json
    # run_query_matching_pipeline("/data/sanglei/Anti-patternRAG/vectorstore", "/data/sanglei/Anti-patternRAG/query", 5)
    # run_embedding_pipeline("/data/sanglei/Anti-patternRAG/data/CH/kafka/commit_1000/6/kafka_6_CH_chunk.json")
    # run_embedding_pipeline("/data/sanglei/Anti-patternRAG/data/CH/kafka/commit_1000/6/kafka_6_CH_chunk.json")


    # 进行 AWD chunk
    chunk_all_cases(Path(DATA_DIR), "AWD")
    # 对 chunk 的结果进行 embedding
    # embedding_all_chunks(Path(CHUNKS_DATA_DIR), VECTORSTORE_DATA_DIR, "AWD")
    # 直接对向量数据库的内容按照 CODE 和 TEXT 进行自评分
    # batch_process_vectorstore_query(vectorstore_path, "MH")
    # 对query 进行 chunk、embedding，并且进行最后的层级评分排序得到结果。
    # 结果存储在 query/vectorstore/aggregated_result.json
    # run_query_matching_pipeline("/data/sanglei/Anti-patternRAG/vectorstore", "/data/sanglei/Anti-patternRAG/query", 5)
    # run_embedding_pipeline("/data/sanglei/Anti-patternRAG/data/CH/kafka/commit_1000/6/kafka_6_CH_chunk.json")
    # run_embedding_pipeline("/data/sanglei/Anti-patternRAG/data/CH/kafka/commit_1000/6/kafka_6_CH_chunk.json")
