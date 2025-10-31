from config.settings import ANTIPATTERN_TYPE, CHUNK_TYPE_WEIGHT_PATH
from retriever.init_vectprstpre import match_query_to_candidate_chunks
from retriever.query_matcher import load_query_chunks, load_query_embeddings
from retriever.retriever_utils import aggregate_topk_from_score_files_with_weights


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

    # # 3 遍历其中的每个 chunk_type，加载对应的向量
    # # 4 与 merged_vectorstore_dir 中的 candidate chunks 做相似度匹配
    # # 5 聚合相似度结果，按 group_id 打分
    # # 6 每个 chunk_type 保存一个 match_scores.json 到 query vectorstore 的路径下
    # score_files = match_query_to_candidate_chunks(query_embedding_path, merge_vectorstore_dir)

    # # 7 根据不同的得分策略来得到最相似的 top_k 个结果
    # result = aggregate_topk_from_score_files_with_weights(score_files, CHUNK_TYPE_WEIGHT_PATH)
    # print(" top_k 个 结果：(group_id, score): ", result)

