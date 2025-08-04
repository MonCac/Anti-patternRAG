import uuid
from pathlib import Path
from typing import Union

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