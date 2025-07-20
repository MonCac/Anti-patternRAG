import os
from pathlib import Path
from typing import List, Union

from ast_chunk_schema import ASTChunk
from splitter.ch_ast_splitter.ast_extractor import extract_superclass_chunks, extract_subclass_chunks
from splitter.ch_ast_splitter.base_chunk import BaseChunk
from splitter.ch_ast_splitter.json_processor import load_case_info
from config.settings import DATA_DIR
from splitter.ch_ast_splitter.llm_chunk_analyzer import llm_analyze_superclass, llm_analyze_subclass
from splitter.utils import parse_line_range


def split_ch_case_into_chunks(base_dir: Union[str, Path]) -> List[BaseChunk]:
    """
    主函数：从一个 CH 案例文件夹中自动定位 JSON 和 Java 文件，抽取 AST 和分析块
    :param base_dir: 指向某个具体 `{id}` 案例文件夹（包含 before/ 与 .json）
    :return: List[ASTChunk]，每个父子子子块
    """
    base_dir = Path(base_dir)

    # 找到 JSON 文件（一个案例文件夹应该只有一个 .json）
    json_files = list(base_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON file found in {base_dir}")
    if len(json_files) > 1:
        raise ValueError(f"Multiple JSON files found in {base_dir}, expected only one.")

    json_path = json_files[0]
    case = load_case_info(json_path)

    # 解析 2 个 Java 文件路径, 构建 Java 文件的完整路径（from before/ 目录）
    java_base_dir = base_dir / "before"
    super_path = os.path.join(java_base_dir, case.super_class_path)
    sub_path = os.path.join(java_base_dir, case.sub_class_path)

    with open(super_path, 'r', encoding='utf-8') as f:
        super_code = f.read()

    with open(sub_path, 'r', encoding='utf-8') as f:
        sub_code = f.read()

    # 提取位置信息（仅使用第一个调用）
    snippet = case.code_snippets[0]
    parent_method_loc = parse_line_range(snippet.parent_method.location)
    child_method_loc = parse_line_range(snippet.child_method.location)
    invocation_loc = parse_line_range(snippet.invocation.location)

    # 提取代码片段
    parent_method_code = snippet.parent_method.code
    child_method_code = snippet.child_method.code
    invocation_code = snippet.invocation.code

    # ---- SuperClass 的子块 ----
    super_chunks: List[BaseChunk] = []
    super_chunks = extract_superclass_chunks(super_code, super_path, parent_method_loc, invocation_loc)
    super_chunks.extend(llm_analyze_superclass(super_path, parent_method_code, invocation_code))

    # ---- SubClass 的子块 ----
    sub_chunks: List[BaseChunk] = []
    sub_chunks = extract_subclass_chunks(sub_code, sub_path, child_method_loc)
    sub_chunks.extend(llm_analyze_subclass(sub_path, child_method_code))

    # ---- 整合所有 chunk ----
    all_chunks = super_chunks + sub_chunks
    print(all_chunks)
    return all_chunks


if __name__ == "__main__":
    split_ch_case_into_chunks(Path(DATA_DIR) / "kafka" / "commit_1000" / "6")