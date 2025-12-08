import json
import pickle
from collections import defaultdict
from pathlib import Path
from typing import List, Tuple

import faiss
from langchain_community.vectorstores import Chroma
import numpy as np
from unicodedata import category

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


def load_faiss_index_and_metadata(idx_path: Path):
    index = faiss.read_index(str(idx_path))
    meta_path = idx_path.parent / "metadata.pkl"
    with open(meta_path, "rb") as f:
        metadata = pickle.load(f)
    return index, metadata


def l2_distance(vec1, vec2):
    return np.linalg.norm(vec1 - vec2)


def cosine_similarity(vec1, vec2):
    v1 = vec1 / (np.linalg.norm(vec1) + 1e-10)
    v2 = vec2 / (np.linalg.norm(vec2) + 1e-10)
    return np.dot(v1, v2)


def match_query_to_candidate_chunks_faiss(query_dir: str, merged_dir: str):
    query_dir = Path(query_dir)
    merged_dir = Path(merged_dir)
    score_files = []

    all_scores = defaultdict(lambda: {"CODE": defaultdict(list), "TEXT": defaultdict(list)})
    group_ids = {}
    folder_paths = {}  # 新增 dict 存储 folder_path

    for category in ["CODE", "TEXT"]:
        query_category_path = query_dir / category
        query_idx_path = query_category_path / "faiss_index.idx"
        query_meta_path = query_category_path / "metadata.pkl"
        if not query_idx_path.exists() or not query_meta_path.exists():
            print(f"[SKIP] Missing query index or metadata for category: {category}")
            continue

        query_index, query_metadata = load_faiss_index_and_metadata(query_idx_path)

        chunk_type_to_query_idxs = defaultdict(list)
        for i, meta in enumerate(query_metadata):
            ct = meta.get("chunk_type")
            if not ct:
                print(f"[WARN] query metadata idx={i} missing chunk_type, skip")
                continue
            chunk_type_to_query_idxs[ct].append(i)

        candidate_base_path = merged_dir / category
        if not candidate_base_path.exists():
            print(f"[WARN] Candidate base path missing for category: {category}")
            continue

        candidate_idx_files = list(candidate_base_path.rglob("faiss_index.idx"))
        print(f"[INFO] Found {len(candidate_idx_files)} candidate idx files for category {category}")

        for candidate_idx_path in candidate_idx_files:
            candidate_dir = candidate_idx_path.parent
            candidate_meta_path = candidate_dir / "metadata.pkl"

            candidate_index, candidate_metadata = load_faiss_index_and_metadata(candidate_idx_path)

            chunk_type_to_candidate_idxs = defaultdict(list)
            for i, meta in enumerate(candidate_metadata):
                ct = meta.get("chunk_type")
                if not ct:
                    print(f"[WARN] candidate metadata idx={i} missing chunk_type, skip")
                    continue
                chunk_type_to_candidate_idxs[ct].append(i)

            try:
                relative_candidate_path = candidate_dir.relative_to(candidate_base_path)
            except Exception as e:
                print(f"[ERROR] candidate_dir.relative_to failed: {candidate_dir} with {e}")
                relative_candidate_path = candidate_dir.name  # 兜底

            rel_path_str = str(relative_candidate_path)

            # 取 group_id（同一个文件相同）
            if rel_path_str not in group_ids:
                if candidate_metadata and "group_id" in candidate_metadata[0]:
                    group_ids[rel_path_str] = candidate_metadata[0]["group_id"]
                else:
                    group_ids[rel_path_str] = None

            # 取 folder_path
            if rel_path_str not in folder_paths and candidate_metadata:
                meta0 = candidate_metadata[0]
                # 这几个字段你说的，安全取
                antipattern_type = meta0.get("antipattern_type", "")
                project_name = meta0.get("project_name", "")
                commit_number = meta0.get("commit_number", "")
                id_ = meta0.get("id", "")
                folder_path = Path("data") / antipattern_type / project_name / commit_number / id_
                folder_paths[rel_path_str] = str(folder_path).replace("\\", "/")  # 兼容windows路径

            print(
                f"\n[MATCH] Category={category}, CandidateDir={candidate_dir}, QueryVectors={query_index.ntotal}")

            all_chunk_types = set(chunk_type_to_query_idxs.keys()) & set(chunk_type_to_candidate_idxs.keys())

            for ct in all_chunk_types:
                query_idxs = chunk_type_to_query_idxs[ct]
                candidate_idxs = chunk_type_to_candidate_idxs[ct]

                if len(query_idxs) != len(candidate_idxs):
                    print(
                        f"[WARN] chunk_type {ct} query idxs({len(query_idxs)}) != candidate idxs({len(candidate_idxs)})")

                for qi, ci in zip(query_idxs, candidate_idxs):
                    query_vec = query_index.reconstruct(qi)
                    candidate_vec = candidate_index.reconstruct(ci)

                    if category == "TEXT":
                        sim = cosine_similarity(query_vec, candidate_vec)
                        score = (sim + 1) / 2
                    else:
                        dist = l2_distance(query_vec, candidate_vec)
                        score = 1 / (1 + dist)

                    score = float(score)

                    candidate_meta = candidate_metadata[ci]
                    all_scores[rel_path_str][category][f"query_{qi}"].append({
                        "chunk_type": ct,
                        "score": score
                    })

    merged_scores_dir = query_dir / "merged_match_scores"
    merged_scores_dir.mkdir(parents=True, exist_ok=True)

    for rel_path_str, category_scores in all_scores.items():
        group_id = group_ids.get(rel_path_str)
        folder_path = folder_paths.get(rel_path_str, "")

        combined_results = {
            "group_id": group_id,
            "folder_path": folder_path,  # 新加字段
            "CODE": {},
            "TEXT": {}
        }

        for cat in ["CODE", "TEXT"]:
            cat_scores = category_scores.get(cat, {})
            for qk, matches in cat_scores.items():
                combined_results[cat][qk] = matches

        output_file = merged_scores_dir / f"{rel_path_str.replace('/', '_')}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(combined_results, f, indent=2, ensure_ascii=False)

        print(f"[SAVE] Combined match scores saved to: {output_file}")
        score_files.append(output_file)

    return merged_scores_dir


def match_merged_chunks_faiss(merged_dir: str, antipattern_type: str):
    merged_dir = Path(merged_dir)
    score_files = []

    group_ids = {}
    folder_paths = {}

    base_output_dir = Path("tmp/merged_match_scores")

    # 先收集所有 candidates，不分 CODE 和 TEXT
    candidates = []

    for category in ["CODE", "TEXT"]:
        category_base_path = merged_dir / category
        print(f"category_base_path: {category_base_path}")
        if not category_base_path.exists():
            print(f"[WARN] Category base path missing: {category}")
            continue

        candidate_idx_files = list(category_base_path.rglob("faiss_index.idx"))
        print(f"[INFO] Found {len(candidate_idx_files)} candidate idx files for category {category}")

        for candidate_idx_path in candidate_idx_files:
            candidate_dir = candidate_idx_path.parent
            candidate_index, candidate_metadata = load_faiss_index_and_metadata(candidate_idx_path)

            chunk_type_to_candidate_idxs = defaultdict(list)
            for i, meta in enumerate(candidate_metadata):
                ct = meta.get("chunk_type")
                if not ct:
                    print(f"[WARN] candidate metadata idx={i} missing chunk_type, skip")
                    continue
                chunk_type_to_candidate_idxs[ct].append(i)

            try:
                relative_candidate_path = candidate_dir.relative_to(category_base_path)
            except Exception as e:
                print(f"[ERROR] candidate_dir.relative_to failed: {candidate_dir} with {e}")
                relative_candidate_path = candidate_dir.name

            rel_path_str = str(relative_candidate_path)

            top_level = rel_path_str.split("/", 1)[0]
            if top_level != antipattern_type:
                continue

            if rel_path_str not in group_ids:
                if candidate_metadata and "group_id" in candidate_metadata[0]:
                    group_ids[rel_path_str] = candidate_metadata[0]["group_id"]
                else:
                    group_ids[rel_path_str] = None

            if rel_path_str not in folder_paths and candidate_metadata:
                meta0 = candidate_metadata[0]
                antipattern_type = meta0.get("antipattern_type", "")
                project_name = meta0.get("project_name", "")
                commit_number = meta0.get("commit_number", "")
                id_ = meta0.get("id", "")
                folder_path = Path(antipattern_type) / project_name / commit_number / id_
                folder_paths[rel_path_str] = str(folder_path).replace("\\", "/")

            # 找 candidates 中是否已经有此 rel_path_str 记录，没有就创建新字典，存多个类别信息
            exist = next((c for c in candidates if c["rel_path_str"] == rel_path_str), None)
            if exist:
                # 如果已经有此候选，更新此类别的index和chunk_type索引
                exist["index_" + category] = candidate_index
                exist["chunk_type_to_candidate_idxs_" + category] = chunk_type_to_candidate_idxs
            else:
                candidates.append({
                    "rel_path_str": rel_path_str,
                    "candidate_dir": candidate_dir,
                    "metadata": candidate_metadata,
                    "index_" + category: candidate_index,
                    "chunk_type_to_candidate_idxs_" + category: chunk_type_to_candidate_idxs
                })

    # 现在 candidates 里每条记录都有 CODE 和 TEXT 对应的索引和 chunk_type 索引
    for i, query_cand in enumerate(candidates):
        for j, candidate_cand in enumerate(candidates):
            if i == j:
                continue  # 跳过自己匹配自己

            print(f"\n[MATCH] Query={query_cand['candidate_dir']}, Candidate={candidate_cand['candidate_dir']}")

            combined_results = {
                "group_id": group_ids.get(candidate_cand["rel_path_str"]),
                "folder_path": folder_paths.get(candidate_cand["rel_path_str"], ""),
                "CODE": {},
                "TEXT": {}
            }

            for category in ["CODE", "TEXT"]:
                query_index = query_cand.get("index_" + category)
                candidate_index = candidate_cand.get("index_" + category)
                chunk_type_to_query_idxs = query_cand.get("chunk_type_to_candidate_idxs_" + category, defaultdict(list))
                chunk_type_to_candidate_idxs = candidate_cand.get("chunk_type_to_candidate_idxs_" + category, defaultdict(list))

                if not query_index or not candidate_index:
                    # 有可能某类别缺失，跳过该类别
                    continue

                all_chunk_types = set(chunk_type_to_query_idxs.keys()) & set(chunk_type_to_candidate_idxs.keys())

                for ct in all_chunk_types:
                    query_idxs = chunk_type_to_query_idxs[ct]
                    candidate_idxs = chunk_type_to_candidate_idxs[ct]

                    if len(query_idxs) != len(candidate_idxs):
                        print(f"[WARN] chunk_type {ct} query idxs({len(query_idxs)}) != candidate idxs({len(candidate_idxs)})")

                    for qi, ci in zip(query_idxs, candidate_idxs):
                        query_vec = query_index.reconstruct(qi)
                        candidate_vec = candidate_index.reconstruct(ci)

                        if category == "TEXT":
                            sim = cosine_similarity(query_vec, candidate_vec)
                            score = (sim + 1) / 2
                        else:
                            dist = l2_distance(query_vec, candidate_vec)
                            score = 1 / (1 + dist)

                        score = float(score)

                        key = f"query_{qi}"
                        if key not in combined_results[category]:
                            combined_results[category][key] = []

                        combined_results[category][key].append({
                            "chunk_type": ct,
                            "score": score
                        })

            # 存文件
            folder_path = folder_paths.get(query_cand["rel_path_str"], "")
            output_dir = base_output_dir / folder_path
            output_dir.mkdir(parents=True, exist_ok=True)

            candidate_name = candidate_cand["rel_path_str"].replace("/", "_")
            output_file = output_dir / f"{candidate_name}.json"

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(combined_results, f, indent=2, ensure_ascii=False)

            print(f"[SAVE] Match scores saved to: {output_file}")
            score_files.append(output_file)

    return base_output_dir


def match_merged_chunks_faiss_ablation(merged_dir: str, antipattern_type: str):
    merged_dir = Path(merged_dir)
    score_files = []

    group_ids = {}
    folder_paths = {}

    base_output_dir = Path("tmp_ablation/merged_match_scores")
    candidates = []
    category = "CODE"

    category_base_path = merged_dir / f"{category}"
    if not category_base_path.exists():
        raise FileNotFoundError(f"[WARN] Category base path missing: {category}")

    candidate_idx_files = list(category_base_path.rglob("faiss_index.idx"))
    print(f"[INFO] Found {len(candidate_idx_files)} candidate idx files for category {category}")
    for candidate_idx_path in candidate_idx_files:
        candidate_dir = candidate_idx_path.parent
        candidate_index, candidate_metadata = load_faiss_index_and_metadata(candidate_idx_path)

        chunk_type_to_candidate_idxs = defaultdict(list)
        for i, meta in enumerate(candidate_metadata):
            ct = meta.get("chunk_type")
            if not ct:
                print(f"[WARN] candidate metadata idx={i} missing chunk_type, skip")
                continue
            chunk_type_to_candidate_idxs[ct].append(i)

        try:
            relative_candidate_path = candidate_dir.relative_to(category_base_path)
        except Exception as e:
            print(f"[ERROR] candidate_dir.relative_to failed: {candidate_dir} with {e}")
            relative_candidate_path = candidate_dir.name

        rel_path_str = str(relative_candidate_path)

        top_level = rel_path_str.split("/", 1)[0]
        if top_level != antipattern_type:
            continue

        if rel_path_str not in group_ids:
            if candidate_metadata and "group_id" in candidate_metadata[0]:
                group_ids[rel_path_str] = candidate_metadata[0]["group_id"]
            else:
                group_ids[rel_path_str] = None

        if rel_path_str not in folder_paths and candidate_metadata:
            meta0 = candidate_metadata[0]
            antipattern_type = meta0.get("antipattern_type", "")
            project_name = meta0.get("project_name", "")
            commit_number = meta0.get("commit_number", "")
            id_ = meta0.get("id", "")
            folder_path = Path(antipattern_type) / project_name / commit_number / id_
            folder_paths[rel_path_str] = str(folder_path).replace("\\", "/")

            # 找 candidates 中是否已经有此 rel_path_str 记录，没有就创建新字典，存多个类别信息
            exist = next((c for c in candidates if c["rel_path_str"] == rel_path_str), None)
            if exist:
                # 如果已经有此候选，更新此类别的index和chunk_type索引
                exist["index_" + category] = candidate_index
                exist["chunk_type_to_candidate_idxs_" + category] = chunk_type_to_candidate_idxs
            else:
                candidates.append({
                    "rel_path_str": rel_path_str,
                    "candidate_dir": candidate_dir,
                    "metadata": candidate_metadata,
                    "index_" + category: candidate_index,
                    "chunk_type_to_candidate_idxs_" + category: chunk_type_to_candidate_idxs
                })

    # 现在 candidates 里每条记录都有 CODE 和 TEXT 对应的索引和 chunk_type 索引
    for i, query_cand in enumerate(candidates):
        for j, candidate_cand in enumerate(candidates):
            if i == j:
                continue  # 跳过自己匹配自己

            print(f"\n[MATCH] Query={query_cand['candidate_dir']}, Candidate={candidate_cand['candidate_dir']}")

            combined_results = {
                "group_id": group_ids.get(candidate_cand["rel_path_str"]),
                "folder_path": folder_paths.get(candidate_cand["rel_path_str"], ""),
                "CODE": {}
            }

            for category in ["CODE"]:
                query_index = query_cand.get("index_" + category)
                candidate_index = candidate_cand.get("index_" + category)
                chunk_type_to_query_idxs = query_cand.get("chunk_type_to_candidate_idxs_" + category, defaultdict(list))
                chunk_type_to_candidate_idxs = candidate_cand.get("chunk_type_to_candidate_idxs_" + category,
                                                                  defaultdict(list))

                if not query_index or not candidate_index:
                    # 有可能某类别缺失，跳过该类别
                    continue

                all_chunk_types = set(chunk_type_to_query_idxs.keys()) & set(chunk_type_to_candidate_idxs.keys())

                for ct in all_chunk_types:
                    query_idxs = chunk_type_to_query_idxs[ct]
                    candidate_idxs = chunk_type_to_candidate_idxs[ct]

                    if len(query_idxs) != len(candidate_idxs):
                        print(
                            f"[WARN] chunk_type {ct} query idxs({len(query_idxs)}) != candidate idxs({len(candidate_idxs)})")

                    for qi, ci in zip(query_idxs, candidate_idxs):
                        query_vec = query_index.reconstruct(qi)
                        candidate_vec = candidate_index.reconstruct(ci)

                        dist = l2_distance(query_vec, candidate_vec)
                        score = 1 / (1 + dist)

                        score = float(score)

                        key = f"query_{qi}"
                        if key not in combined_results[category]:
                            combined_results[category][key] = []

                        combined_results[category][key].append({
                            "chunk_type": ct,
                            "score": score
                        })

            # 存文件
            folder_path = folder_paths.get(query_cand["rel_path_str"], "")
            output_dir = base_output_dir / folder_path
            output_dir.mkdir(parents=True, exist_ok=True)

            candidate_name = candidate_cand["rel_path_str"].replace("/", "_")
            output_file = output_dir / f"{candidate_name}.json"

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(combined_results, f, indent=2, ensure_ascii=False)

            print(f"[SAVE] Match scores saved to: {output_file}")
            score_files.append(output_file)

    return base_output_dir


if __name__ == "__main__":
    match_merged_chunks_faiss("/Users/moncheri/Downloads/main/重构/反模式修复数据集构建/RefactorRAG/Anti-PatternRAG/tmp/vectorstore")
