import json
import os
from pathlib import Path
from typing import List, Union, Any
from splitter.ch_ast_splitter.ast_extractor import extract_superclass_chunks, extract_subclass_chunks
from splitter.ch_ast_splitter.base_chunk_schema import BaseChunk
from splitter.ch_ast_splitter.json_processor import load_case_info
from config.settings import DATA_DIR
from splitter.ch_ast_splitter.llm_chunk_analyzer import llm_analyze_superclass, llm_analyze_subclass
from splitter.utils import parse_line_range
from config.settings import ANTIPATTERN_TYPE


def build_chunks(base_dir: Union[str, Path], antipattern_type, group_id):
    """
    主函数：从一个 CH 案例文件夹中自动定位 JSON 和 Java 文件，抽取 AST 和分析块
    :param base_dir: 指向某个具体 `{id}` 案例文件夹（包含 before/ 与 .json）
    :param group_id:
    :dict[str, Union[str, list, Any]]，每个父子子子块
    """
    base_dir = Path(base_dir)

    # 得到 chunk 的 metadata 内容，如果是构建 query 的chunk，即 group_id < 0，则其他内容都为-1
    if group_id < 0:
        antipattern_type = antipattern_type
        project_name = -1
        commit_number = -1
        case_id = -1
    else:
        # 提取路径倒数四级
        parts = base_dir.parts[-4:]  # 获取倒数4个路径名
        antipattern_type, project_name, commit_number, case_id = parts

    # 找到 JSON 文件（一个案例文件夹应该只有一个 *antipattern.json）
    json_files = list(base_dir.glob("*antipattern.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON name *antipattern.json file found in {base_dir}")

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

    json_chunks = [chunk.to_dict() for chunk in all_chunks]

    result = {
        "antipattern_type": antipattern_type,
        "project_name": project_name,
        "commit_number": commit_number,
        "id": case_id,
        "group_id": group_id,
        "chunks": json_chunks
    }

    if group_id < 0:
        chunk_filename = "query_chunk.json"
    else:
        # 构造输出路径：和 JSON 文件在同一目录，命名为 `{project}_{case_id}_{antipattern}_chunk.json`
        chunk_filename = f"{project_name}_{case_id}_{antipattern_type}_chunk.json"
    output_path = base_dir / chunk_filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"分块结果已保存至: {output_path}")
    return result, output_path


if __name__ == "__main__":
    build_chunks(Path(DATA_DIR) / "kafka" / "commit_1000" / "6", 0)
