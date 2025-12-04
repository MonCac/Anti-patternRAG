import json
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Union, List, Tuple, Dict, Any

from langchain_community.vectorstores import Chroma


def collect_all_chroma_paths(base_dir: Union[str, Path]):
    """
    遍历 base_dir，找出所有 CODE / TEXT 的 chroma 向量库路径
    返回 dict: {"CODE": [Path1, Path2, ...], "TEXT": [...]}
    """
    result = {"CODE": [], "TEXT": []}
    for path in base_dir.rglob("*"):
        if path.name in ["CODE", "TEXT"] and path.is_dir():
            result[path.name].append(path)
    return result["CODE"], result["TEXT"]


def save_vectorstore(target_path: Path, data: dict, embedding_model):
    print(f"[SAVE] Writing to: {target_path}")
    if not target_path.exists():
        target_path.mkdir(parents=True, exist_ok=True)

    db = Chroma(
        embedding_function=embedding_model,
        persist_directory=str(target_path)
    )

    add_embeddings(
        db,
        docs=data["docs"],
        embeddings=data["embeddings"],
        metadatas=data["metadatas"]
    )
    db.persist()


def add_embeddings(db, docs, embeddings, metadatas):
    # 生成id，确保唯一
    ids = [str(uuid.uuid4()) for _ in docs]

    # 底层collection直接upsert
    # 注意：此处访问的是受保护成员 _collection，langchain目前没有公开接口直接插入已有embeddings
    db._collection.upsert(
        embeddings=embeddings,
        documents=docs,
        metadatas=metadatas,
        ids=ids
    )


def aggregate_topk_from_merged_match_scores(merged_scores_dir: Path, weight_file: Path, top_k: int = 5) -> List[Tuple[str, float, str]]:
    scores_by_group = defaultdict(float)
    group_to_path = {}

    # 加载chunk_type权重
    with open(weight_file, "r", encoding="utf-8") as f:
        chunk_weights = json.load(f)

    merged_scores_dir = Path(merged_scores_dir)
    json_files = list(merged_scores_dir.glob("*.json"))

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load {json_file}: {e}")
            continue

        group_id = data.get("group_id")
        folder_path = data.get("folder_path", "")

        if group_id is None:
            print(f"[WARN] No group_id in {json_file}, skip")
            continue

        # 记录 group_id -> folder_path，优先第一个出现的路径
        if group_id not in group_to_path and folder_path:
            group_to_path[group_id] = folder_path

        # CODE 和 TEXT 两部分都遍历
        for category in ["CODE", "TEXT"]:
            category_scores = data.get(category, {})
            for query_id, matches in category_scores.items():
                for match in matches:
                    chunk_type = match.get("chunk_type")
                    score = match.get("score", 0)
                    weight = chunk_weights.get(chunk_type, 0.1)  # 默认0.1

                    scores_by_group[group_id] += score * weight

    # 按总分排序，降序
    sorted_scores = sorted(scores_by_group.items(), key=lambda x: x[1], reverse=True)

    # 返回 (group_id, score, folder_path)
    results = []
    for group_id, score in sorted_scores[:top_k]:
        path = group_to_path.get(group_id, "")
        results.append((group_id, score, path))

    return results


def read_and_save_files_in_paths(
    results: List[Tuple[str, float, str]],
    output_dir: Path | str,
    output_filename: str = "aggregated_results.json"
) -> Dict[str, Dict[str, Any]]:
    """
    遍历每个结果中的path，读取该目录下所有文件内容，
    并将最终结果保存为一个JSON文件。

    参数:
      results: List of tuples like (group_id, score, path_str)
      output_dir: Path to directory where the JSON file will be saved
      output_filename: 输出JSON文件名，默认为"aggregated_results.json"

    返回:
      dict keyed by group_id, value is dict with keys:
        - "score": float
        - "path": str
        - "files": dict, key=relative filepath (str), value=file content (str)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data = {}

    for group_id, score, path_str in results:
        base_path = Path(path_str)
        if not base_path.exists() or not base_path.is_dir():
            print(f"[WARN] Path does not exist or is not a directory: {path_str}")
            continue

        files_content = {}

        for file_path in base_path.rglob("*"):
            if file_path.is_file():
                try:
                    rel_path = file_path.relative_to(base_path).as_posix()
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    files_content[rel_path] = content
                except Exception as e:
                    print(f"[ERROR] Failed to read file {file_path}: {e}")

        data[group_id] = {
            "score": score,
            "path": path_str,
            "files": files_content
        }

    output_file = output_dir / output_filename
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[INFO] Aggregated results saved to {output_file}")
    return data


def read_and_aggregated_results_in_paths(
    results: List[Tuple[str, float, str]],
    output_dir: Path | str,
    output_filename: str = "aggregated_results.json"
) -> Dict[str, Dict[str, Any]]:
    """
    遍历每个结果中的path，读取该目录下所有文件内容，
    并将最终结果保存为一个JSON文件。

    参数:
      results: List of tuples like (group_id, score, path_str)
      output_dir: Path to directory where the JSON file will be saved
      output_filename: 输出JSON文件名，默认为"aggregated_results.json"

    返回:
      dict keyed by group_id, value is dict with keys:
        - "score": float
        - "path": str
        - "files": dict, key=relative filepath (str), value=file content (str)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data = {}

    for group_id, score, path_str in results:
        data[group_id] = {
            "score": score,
            "path": path_str
        }

    output_file = output_dir / output_filename
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[INFO] Aggregated results saved to {output_file}")
    return data