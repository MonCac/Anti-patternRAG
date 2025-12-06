import json
import os
from pathlib import Path
from typing import List, Union, Any
from splitter.ch_ast_splitter.ast_extractor import extract_superclass_chunks, extract_subclass_chunks, \
    extract_awd_superclass_chunks, extract_awd_subclass_chunks
from splitter.ch_ast_splitter.base_chunk_schema import BaseChunk
from splitter.ch_ast_splitter.json_processor import load_case_info
from config.settings import DATA_DIR
from splitter.ch_ast_splitter.llm_chunk_analyzer import llm_analyze_superclass, llm_analyze_subclass, \
    awd_llm_analyze_subclass
from splitter.utils import parse_line_range


def build_chunks(base_dir: Union[str, Path], antipattern_type, group_id):
    result = ''
    output_path = ''
    match antipattern_type:
        case "CH":
            result, output_path = build_ch_chunks(base_dir, antipattern_type, group_id)
        case "MH":
            result, output_path = build_mh_chunks(base_dir, antipattern_type, group_id)
        case "AWD":
            result, output_path = build_awd_chunks(base_dir, antipattern_type, group_id)

    return result, output_path


def build_ch_chunks(base_dir: Union[str, Path], antipattern_type, group_id):
    """
    主函数：从一个 CH 案例文件夹中自动定位 JSON 和 Java 文件，抽取 AST 和分析块
    :param base_dir: 指向某个具体 `{id}` 案例文件夹（包含 before/ 与 .json）
    :param antipattern_type:
    :param group_id:
    :dict[str, Union[str, list, Any]]，每个父子子子块
    """
    base_dir = Path(base_dir)

    print("enter build_chunks")

    # 得到 chunk 的 metadata 内容，如果是构建 query 的chunk，即 group_id < 0，则其他内容都为-1
    if group_id < 0:
        antipattern_type = antipattern_type
        project_name = -1
        commit_number = -1
        case_id = -1
    else:
        # 提取路径倒数四级
        parts = base_dir.parts[-4:]  # 获取倒数4个路径名
        _, project_name, commit_number, case_id = parts

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
    print("start SuperClass Chunk")
    super_chunks: List[BaseChunk] = []
    super_chunks = extract_superclass_chunks(super_code, super_path, parent_method_loc, invocation_loc)
    super_chunks.extend(llm_analyze_superclass(super_path, parent_method_code, invocation_code))

    # ---- SubClass 的子块 ----
    print("start SubClass Chunk")
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
        output_dir = Path("query")
    else:
        # 构造输出路径：和 JSON 文件在同一目录，命名为 `{project}_{case_id}_{antipattern}_chunk.json`
        chunk_filename = f"{project_name}_{commit_number}_{case_id}_{antipattern_type}_chunk.json"
        output_dir = Path(f"tmp/chunks/{antipattern_type}")
    output_dir.mkdir(parents=True, exist_ok=True)  # 自动创建目录
    output_path = output_dir / chunk_filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"分块结果已保存至: {output_path}")
    return result, output_path


def build_mh_chunks(base_dir: Union[str, Path], antipattern_type, group_id):
    """
    主函数：从一个 MH 案例文件夹中自动定位 JSON 和 Java 文件，抽取 AST 和分析块
    :param base_dir: 指向某个具体 `{id}` 案例文件夹（包含 before/ 与 .json）
    :param antipattern_type:
    :param group_id:
    :dict[str, Union[str, list, Any]]，每个父子子子块
    """
    base_dir = Path(base_dir)

    print("enter build_chunks")

    # 得到 chunk 的 metadata 内容，如果是构建 query 的chunk，即 group_id < 0，则其他内容都为-1
    if group_id < 0:
        antipattern_type = antipattern_type
        project_name = -1
        commit_number = -1
        case_id = -1
    else:
        # 提取路径倒数四级
        parts = base_dir.parts[-4:]  # 获取倒数4个路径名
        _, project_name, commit_number, case_id = parts

    # 找到 JSON 文件（一个案例文件夹应该只有一个 *antipattern.json）
    json_files = list(base_dir.glob("*mh_antipattern.json"))
    if len(json_files) != 2:
        raise FileNotFoundError(f"MH case requires exactly 2 *mh_antipattern.json files in {base_dir}")

    # 分别识别 GAP 的和非 GAP 的
    gap_json_path = None
    case_json_path = None
    for p in json_files:
        if "GAP" in p.name:
            gap_json_path = p
        else:
            case_json_path = p

    if gap_json_path is None:
        raise FileNotFoundError("GAP_*mh_antipattern.json not found")
    if case_json_path is None:
        raise FileNotFoundError("*mh_antipattern.json (non-GAP) not found")

    before_dir = base_dir / "before"
    yaml_files = list(before_dir.glob("*.yaml"))
    if len(yaml_files) != 1:
        raise FileNotFoundError(
            f"MH case requires exactly one YAML file in before/, found {len(yaml_files)}"
        )
    yaml_path = yaml_files[0]

    fdesc_path = base_dir / "llm_function_description" / "before.json"
    if not fdesc_path.exists():
        raise FileNotFoundError(f"Missing llm_function_description/before.json in {base_dir}")

    chunks = []

    # 1) GAP JSON chunk
    chunks.append({
        "chunk_type": "mh_gap_json",
        "source_path": str(gap_json_path),
        "ast_subtree": gap_json_path.read_text(encoding="utf-8")
    })

    # 2) Case JSON chunk
    chunks.append({
        "chunk_type": "mh_case_json",
        "source_path": str(case_json_path),
        "ast_subtree": case_json_path.read_text(encoding="utf-8")
    })

    # 3) YAML chunk
    chunks.append({
        "chunk_type": "mh_yaml",
        "source_path": str(yaml_path),
        "ast_subtree": yaml_path.read_text(encoding="utf-8")
    })

    # 4) Function description (text chunk)
    chunks.append({
        "chunk_type": "mh_function_description",
        "source_path": str(fdesc_path),
        "llm_description": fdesc_path.read_text(encoding="utf-8")
    })

    result = {
        "antipattern_type": antipattern_type,
        "project_name": project_name,
        "commit_number": commit_number,
        "id": case_id,
        "group_id": group_id,
        "chunks": chunks
    }

    if group_id < 0:
        chunk_filename = "query_chunk.json"
        output_dir = Path("query")
    else:
        # 构造输出路径：和 JSON 文件在同一目录，命名为 `{project}_{case_id}_{antipattern}_chunk.json`
        chunk_filename = f"{project_name}_{commit_number}_{case_id}_{antipattern_type}_chunk.json"
        output_dir = Path(f"tmp/chunks/{antipattern_type}")
    output_dir.mkdir(parents=True, exist_ok=True)  # 自动创建目录
    output_path = output_dir / chunk_filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"分块结果已保存至: {output_path}")
    return result, output_path


def build_awd_chunks(base_dir: Union[str, Path], antipattern_type, group_id):
    """
    主函数：从一个 AWD 案例文件夹中自动定位 JSON 和 Java 文件，抽取 AST 和分析块
    :param base_dir: 指向某个具体 `{id}` 案例文件夹（包含 before/ 与 .json）
    :param antipattern_type:
    :param group_id:
    :dict[str, Union[str, list, Any]]，每个父子子子块
    """
    base_dir = Path(base_dir)

    print("enter build_chunks")

    # 得到 chunk 的 metadata 内容，如果是构建 query 的chunk，即 group_id < 0，则其他内容都为-1
    if group_id < 0:
        antipattern_type = antipattern_type
        project_name = -1
        commit_number = -1
        case_id = -1
    else:
        # 提取路径倒数四级
        parts = base_dir.parts[-4:]  # 获取倒数4个路径名
        _, project_name, commit_number, case_id = parts

    # 找到 JSON 文件（一个案例文件夹应该只有一个 *antipattern.json）
    json_files = list(base_dir.glob("*_awd_antipattern.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON name *antipattern.json file found in {base_dir}")

    json_path = json_files[0]

    with open(json_path, "r", encoding="utf-8") as f:
        json_content = json.load(f)

    # 解析 3 个 Java 文件路径,
    details = json_content["details"]
    java_base_dir = base_dir / "before"
    llm_before_path = base_dir / "llm_function_description"

    client_path = details["clientClass2superType"]["fromFile"]
    super_path = details["clientClass2superType"]["toFile"]
    sub_path = details["clientClass2subType"]["toFile"]

    client_path_rel = os.path.join(java_base_dir, client_path)
    super_path_rel = os.path.join(java_base_dir, super_path)
    sub_path_rel = os.path.join(java_base_dir, sub_path)
    llm_before_path = os.path.join(llm_before_path, "before.json")

    with open(client_path_rel, 'r', encoding='utf-8') as f:
        client_code = f.read()

    with open(super_path_rel, 'r', encoding='utf-8') as f:
        super_code = f.read()

    with open(sub_path_rel, 'r', encoding='utf-8') as f:
        sub_code = f.read()

    with open(llm_before_path, "r", encoding="utf-8") as f:
        llm_before_content = json.load(f)

    # 提取 superType location
    superType_snippets = details["clientClass2superType"]["snippets"][0]
    superType_parent_method_loc = parse_line_range(superType_snippets["parentMethod"]["location"])
    superType_child_method_loc = parse_line_range(superType_snippets["childMethod"]["location"])
    superType_invocation_loc = parse_line_range(superType_snippets["invocation"]["location"])

    # 提取 subType location
    subType_snippets = details["clientClass2subType"]["snippets"][0]
    subType_parent_method_loc = parse_line_range(subType_snippets["parentMethod"]["location"])
    subType_child_method_loc = parse_line_range(subType_snippets["childMethod"]["location"])
    subType_invocation_loc = parse_line_range(subType_snippets["invocation"]["location"])

    # ---- SuperClass 的子块 ----
    print("start SuperClass Chunk")
    super_chunks: List[BaseChunk] = []
    super_chunks = extract_awd_superclass_chunks(super_code, super_path, client_code, client_path, superType_parent_method_loc, superType_child_method_loc, superType_invocation_loc)
    # ---- SubClass 的子块 ----
    print("start SubClass Chunk")
    sub_chunks: List[BaseChunk] = []
    sub_chunks = extract_awd_subclass_chunks(sub_code, sub_path, client_code, client_path, subType_parent_method_loc, subType_child_method_loc, subType_invocation_loc)

    llm_chunks = awd_llm_analyze_subclass(client_path, super_path, sub_path, llm_before_content)

    # ---- 整合所有 chunk ----
    all_chunks = super_chunks + sub_chunks + llm_chunks
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
        output_dir = Path("query")
    else:
        # 构造输出路径：和 JSON 文件在同一目录，命名为 `{project}_{case_id}_{antipattern}_chunk.json`
        chunk_filename = f"{project_name}_{commit_number}_{case_id}_{antipattern_type}_chunk.json"
        output_dir = Path(f"tmp/chunks/{antipattern_type}")
    output_dir.mkdir(parents=True, exist_ok=True)  # 自动创建目录
    output_path = output_dir / chunk_filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"分块结果已保存至: {output_path}")
    return result, output_path


if __name__ == "__main__":
    build_chunks(Path(DATA_DIR) / "kafka" / "commit_1000" / "6", "CH", 0)
