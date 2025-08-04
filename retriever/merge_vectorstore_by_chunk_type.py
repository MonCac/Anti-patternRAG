from pathlib import Path

from langchain_community.vectorstores import Chroma
from config.settings import CODE_EMBEDDING_MODEL, TEXT_EMBEDDING_MODEL
from embeddings.embedding_utils import init_embedding_model
from retriever.retriever_utils import collect_all_chroma_paths, save_vectorstore


def merge_vectorstore_by_chunk_type(source_root: str):
    source_root = Path(source_root)
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


def write_merged_vectorstore(target_path: Path, data: dict, embedding_model):
    """
    将分组后的 chunk_type 数据写入新的 Chroma 向量库
    """
    if target_path.exists():
        print(f"[SKIP] Already exists: {target_path}")
        return

    print(f"[WRITE] Merging chunk_type => {target_path}")
    target_path.mkdir(parents=True, exist_ok=True)

    chroma_db = Chroma(
        embedding_function=embedding_model,
        persist_directory=str(target_path)
    )
    chroma_db.add_embeddings(
        texts=data["docs"],
        embeddings=data["embeddings"],
        metadatas=data["metadatas"]
    )
    chroma_db.persist()