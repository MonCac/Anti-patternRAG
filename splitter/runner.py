import os
from splitter.strategy_registry import load_splitter_by_mode
from config.settings import ANTIPATTERN_TYPE

antipattern_type = ANTIPATTERN_TYPE


def chunk_all_cases(base_dir, mode="java") -> list:
    """
    扫描所有项目文件夹，提取基础 text-only chunks。
    默认读取 data/{antipattern_type} 路径结构。
    """
    all_chunks = []
    build_chunk = load_splitter_by_mode(mode)
    base_dir = os.path.join(base_dir, antipattern_type)
    for project in os.listdir(base_dir):
        project_path = os.path.join(base_dir, project)
        if not os.path.isdir(project_path):
            continue

        for commit in os.listdir(project_path):
            commit_path = os.path.join(project_path, commit)
            if not os.path.isdir(commit_path):
                continue

            for case_id in os.listdir(commit_path):
                case_path = os.path.join(commit_path, case_id)
                if not os.path.isdir(case_path):
                    continue

                chunk = build_chunk(case_path, case_id)
                all_chunks.append(chunk)

    return all_chunks
