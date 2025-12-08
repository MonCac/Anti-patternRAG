import os
from pathlib import Path

from config.settings import ANTIPATTERN_TYPE, CH_CHUNK_TYPE_WEIGHT_PATH, MH_CHUNK_TYPE_WEIGHT_PATH, \
    AWD_CHUNK_TYPE_WEIGHT_PATH, CH_CHUNK_TYPE_ABLATION_WEIGHT_PATH, MH_CHUNK_TYPE_ABLATION_WEIGHT_PATH, \
    AWD_CHUNK_TYPE_ABLATION_WEIGHT_PATH
from retriever.init_vectprstpre import match_query_to_candidate_chunks_faiss, match_merged_chunks_faiss, \
    match_merged_chunks_faiss_ablation
from retriever.query_matcher import load_query_chunks, load_query_embeddings
from retriever.retriever_utils import aggregate_topk_from_merged_match_scores, read_and_save_files_in_paths, \
    read_and_aggregated_results_in_paths


def run_query_matching_pipeline(merge_vectorstore_dir: str, query_data_dir: str, top_k: int = 5):
    """
    1. 从 query_project_dir 中提取文本/代码块
    2 对其进行 chunk → embedding → 存储为临时 query_vectorstore
    3 遍历其中的每个 chunk_type，加载对应的向量
    4 与 merged_vectorstore_dir 中的 candidate chunks 做相似度匹配
    5 聚合相似度结果，按 group_id 打分
    6 每个 chunk_type 保存一个 match_scores.json 到 query vectorstore 的路径下
    7 根据不同的得分策略来得到最相似的 top_k 个结果
    :param merge_vectorstore_dir: 向量知识库存储路径
    :param query_data_dir: 待检索数据存储路径
    :param top_k: 检索到的最相关数目
    :return:
    """
    print("run run_query_matching_pipeline")
    # 1. 从 query_project_dir 中提取文本/代码块
    _, query_chunk_path = load_query_chunks(query_data_dir, ANTIPATTERN_TYPE)

    # 2 对其进行 chunk → embedding → 存储为临时 query_vectorstore
    query_embedding_path = load_query_embeddings(query_chunk_path, True)
    print(f"query_embedding_path: {query_embedding_path}")

    # 3 遍历其中的每个 chunk_type，加载对应的向量
    # 4 与 merged_vectorstore_dir 中的 candidate chunks 做相似度匹配
    # 5 聚合相似度结果，按 group_id 打分
    # 6 每个 chunk_type 保存一个 match_scores.json 到 query vectorstore 的路径下
    score_files = match_query_to_candidate_chunks_faiss(query_embedding_path, merge_vectorstore_dir)

    # 7 根据不同的得分策略来得到最相似的 top_k 个结果
    result = aggregate_topk_from_merged_match_scores(score_files, CH_CHUNK_TYPE_WEIGHT_PATH)
    print(" top_k 个 结果：(group_id, score): ", result)

    final_result = read_and_save_files_in_paths(result, query_embedding_path)
    print(f"final_result: {final_result}")


def batch_process_vectorstore_query(vectorstore_path, antipattern_type="CH", ablation=False):
    if ablation:
        base_dir = match_merged_chunks_faiss_ablation(vectorstore_path, antipattern_type)
        chunk_type_weight_path = ""
        match antipattern_type:
            case "CH":
                chunk_type_weight_path = CH_CHUNK_TYPE_ABLATION_WEIGHT_PATH
            case "MH":
                chunk_type_weight_path = MH_CHUNK_TYPE_ABLATION_WEIGHT_PATH
            case "AWD":
                chunk_type_weight_path = AWD_CHUNK_TYPE_ABLATION_WEIGHT_PATH
    else:
        base_dir = match_merged_chunks_faiss(vectorstore_path, antipattern_type)
        chunk_type_weight_path = ""
        match antipattern_type:
            case "CH":
                chunk_type_weight_path = CH_CHUNK_TYPE_WEIGHT_PATH
            case "MH":
                chunk_type_weight_path = MH_CHUNK_TYPE_WEIGHT_PATH
            case "AWD":
                chunk_type_weight_path = AWD_CHUNK_TYPE_WEIGHT_PATH

    batch_process_query(base_dir, chunk_type_weight_path, antipattern_type)


def batch_process_query(base_dir: Path, chunk_weight_path: Path, antipattern_type, top_k: int = 5):
    base_dir = Path(base_dir)

    # 找所有最底层文件夹（无子目录的文件夹）
    def find_leaf_dirs(root_dir):
        leaf_dirs = []
        for dirpath, dirnames, filenames in os.walk(root_dir):
            if not dirnames:  # 没有子目录，就是叶子目录
                leaf_dirs.append(Path(dirpath))
        return leaf_dirs

    target_dir = base_dir / antipattern_type
    if not target_dir.exists() or not target_dir.is_dir():
        print(f"{target_dir} 不存在或不是目录")
        return

    leaf_dirs = find_leaf_dirs(target_dir)
    print(f"[INFO] Found {len(leaf_dirs)} leaf directories under {base_dir}")

    all_final_results = {}

    for leaf_dir in leaf_dirs:
        print(f"\n[PROCESS] Processing leaf directory: {leaf_dir}")

        # 1. aggregate_topk_from_merged_match_scores 输入参数是score文件夹路径
        try:
            result = aggregate_topk_from_merged_match_scores(leaf_dir, chunk_weight_path, top_k)
            print(f"[INFO] Top-k results in {leaf_dir}: {result}")
        except Exception as e:
            print(f"[ERROR] Failed aggregate_topk_from_merged_match_scores on {leaf_dir}: {e}")
            continue

        # 2. read_and_save_files_in_paths 输入参数是上一步结果 和 leaf_dir
        try:
            final_result = read_and_aggregated_results_in_paths(result, leaf_dir)
            print(f"[INFO] Final result saved for {leaf_dir}")
            all_final_results[str(leaf_dir)] = final_result
        except Exception as e:
            print(f"[ERROR] Failed read_and_save_files_in_paths on {leaf_dir}: {e}")
            continue

    return all_final_results
