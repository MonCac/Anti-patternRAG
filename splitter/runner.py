from splitter.strategy_registry import load_splitter_by_mode
from utils.utils import iter_case_paths


def chunk_all_cases(base_dir, antipattern_type, mode="ast") -> list:
    all_chunks = []
    group_id = 0
    build_chunks = load_splitter_by_mode(mode)

    for case_path in iter_case_paths(base_dir, antipattern_type):
        chunk, path = build_chunks(case_path, antipattern_type, group_id)
        group_id += 1
        all_chunks.append(chunk)

    return all_chunks
