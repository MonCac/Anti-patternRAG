import os
from pathlib import Path
from typing import Union
from embeddings.build_code_embedding import build_code_embedding
from embeddings.build_text_embedding import build_text_embedding
from config.settings import ANTIPATTERN_TYPE
from utils.utils import exist_chunk_json, iter_case_paths

antipattern_type = ANTIPATTERN_TYPE


def run_embedding_pipeline(chunks_json_path: Union[str, Path], vectorstore_base_path, query: bool = False, ablation: bool = False):
    chunks_json_path = Path(chunks_json_path)

    if not chunks_json_path.exists():
        raise FileNotFoundError(f"Chunk JSON file does not exist: {chunks_json_path}")
    if not ablation:
        print(f" start run     build_text_embedding{chunks_json_path} ")
        build_text_embedding(chunks_json_path, vectorstore_base_path, query)
        print(f"✅ run over    build_text_embedding{chunks_json_path} ")
    print(f" start run     build_code_embedding{chunks_json_path} ")
    path = build_code_embedding(chunks_json_path, vectorstore_base_path, query)
    print(f"✅ run over    build_code_embedding{chunks_json_path} ")

    return path


def embedding_all_chunks(base_dir, vectorstore_base_path, antipattern_type=None, mode="ast", ablation=False):
    """
    遍历 base_dir 下所有 JSON 文件（包括子目录），并对每个 JSON 文件执行 embedding pipeline。

    Args:
        base_dir: 根目录，递归查找 JSON 文件。
        antipattern_type: 可选参数，如果传入，可用于日志或过滤（这里暂不做过滤）。
        mode: 模式参数，传给 pipeline（可扩展）。
    """
    base_dir = os.path.join(base_dir, antipattern_type)
    json_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))

    print(f"[i] Found {len(json_files)} JSON files in {base_dir}")

    for json_path in json_files:
        run_embedding_pipeline(json_path, vectorstore_base_path, ablation=ablation)

    return "✅ EMBEDDING OVER"


if __name__ == "__main__":
    # ✅ 示例调用
    run_embedding_pipeline("/data/sanglei/Anti-patternRAG/data/CH/kafka/commit_1000/6/kafka_6_CH_chunk.json", "tmp/vectorstore")

