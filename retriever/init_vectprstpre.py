import json
from collections import defaultdict
from pathlib import Path
from typing import List, Tuple

from langchain_community.vectorstores import Chroma
from config.settings import CODE_EMBEDDING_MODEL, TEXT_EMBEDDING_MODEL
from embeddings.embedding_utils import init_embedding_model
from retriever.retriever_utils import collect_all_chroma_paths, save_vectorstore


# 该函数可以同时实现初始创建按 chunk_type 分类的向量知识库，也可以实现传入新增的 embeddings 结果存放入 target_root 中
def merge_vectorstore_by_chunk_type(source_root: str, target_root: str = None):
    # eg: source_root = /Users/moncheri/Downloads/main/重构/反模式修复数据集构建/RefactorRAG/Anti-PatternRAG/vectorstore/CH
    # eg: target_root = /Users/moncheri/Downloads/main/重构/反模式修复数据集构建/RefactorRAG/Anti-PatternRAG/vectorstore/merged_vectorstore

    source_root = Path(source_root)
    if target_root is None:
        target_root = source_root.parent / "merged_vectorstore"
        target_root.mkdir(parents=True, exist_ok=True)

    code_paths, text_paths = collect_all_chroma_paths(source_root)
    chroma_paths = {"CODE": code_paths, "TEXT": text_paths}

    for category, paths in chroma_paths.items():
        print(f"\n[PROCESSING] Category: {category}  Total found: {len(paths)}")

        embedding_model = init_embedding_model(
            CODE_EMBEDDING_MODEL if category == "CODE" else TEXT_EMBEDDING_MODEL,
            default_task="code.passage" if category == "CODE" else None
        )

        chunk_type_data = {}

        for chroma_dir in paths:
            print(f"[LOAD] {chroma_dir}")
            db = Chroma(persist_directory=str(chroma_dir), embedding_function=embedding_model)
            data = db.get()
            docs = data["documents"]
            metadatas = data["metadatas"]
            embeddings = data["embeddings"]

            for doc, meta, emb in zip(docs, metadatas, embeddings):
                chunk_type = meta.get("chunk_type")
                if not chunk_type:
                    print(f"[WARN] Missing chunk_type in metadata. Skipping.")
                    continue

                if chunk_type not in chunk_type_data:
                    chunk_type_data[chunk_type] = {"docs": [], "metadatas": [], "embeddings": []}

                chunk_type_data[chunk_type]["docs"].append(doc)
                chunk_type_data[chunk_type]["metadatas"].append(meta)
                chunk_type_data[chunk_type]["embeddings"].append(emb)

        for chunk_type, data in chunk_type_data.items():
            target_path = target_root / category / chunk_type
            save_vectorstore(target_path, data, embedding_model)


def match_query_to_candidate_chunks(query_dir: str, merged_dir: str, top_k: int = 5):
    query_dir = Path(query_dir)
    merged_dir = Path(merged_dir)

    score_files = []  # ← 新增一个列表来收集所有 score 文件路径
    for category in ["CODE", "TEXT"]:
        embedding_model = init_embedding_model(
            CODE_EMBEDDING_MODEL if category == "CODE" else TEXT_EMBEDDING_MODEL,
            default_task="code.passage" if category == "CODE" else None
        )

        query_category_path = query_dir / category
        if not query_category_path.exists():
            print(f"[SKIP] No query data for category: {category}")
            continue

        # 加载 query 向量库（整个 CODE 或 TEXT）
        query_db = Chroma(
            persist_directory=str(query_category_path),
            embedding_function=embedding_model
        )
        query_data = query_db.get()
        query_embeddings = query_data.get("embeddings", [])
        query_metadatas = query_data.get("metadatas", [])

        if not query_embeddings:
            print(f"[WARN] No embeddings found in query for {category}")
            continue

        # 为该 category 准备存储目录
        output_score_dir = query_category_path / "match_scores"
        output_score_dir.mkdir(parents=True, exist_ok=True)

        # 拆分 query embedding 按 chunk_type 分组
        chunktype_to_queries = defaultdict(list)
        for idx, (emb, meta) in enumerate(zip(query_embeddings, query_metadatas)):
            chunk_type = meta.get("chunk_type")
            if not chunk_type:
                print(f"[WARN] Missing chunk_type for query {idx}, skipping.")
                continue
            chunktype_to_queries[chunk_type].append((idx, emb))

        # 对每个 chunk_type 的 query 去 candidate 检索
        for chunk_type, queries in chunktype_to_queries.items():
            candidate_path = merged_dir / category / chunk_type
            if not candidate_path.exists():
                print(f"[WARN] Missing candidate DB for chunk_type: {chunk_type}")
                continue

            candidate_db = Chroma(
                persist_directory=str(candidate_path),
                embedding_function=embedding_model
            )

            print(f"\n[MATCH] Category={category}, ChunkType={chunk_type}, Queries={len(queries)}")

            match_scores = {}  # {query_id: [ {group_id, score}, ... ] }

            for idx, embedding in queries:
                matches = candidate_db.similarity_search_by_vector_with_relevance_scores(embedding, k=top_k)
                match_scores[f"query_{idx}"] = [
                    {"group_id": doc.metadata.get("group_id", ""), "score": 1 - distance}
                    for doc, distance in matches
                ]

            # 保存 match 结果到文件
            score_file = output_score_dir / f"{chunk_type}.json"
            with open(score_file, "w", encoding="utf-8") as f:
                json.dump(match_scores, f, indent=2, ensure_ascii=False)

            print(f"[SAVE] Match scores written to: {score_file}")
            score_files.append(score_file)

    return score_files

