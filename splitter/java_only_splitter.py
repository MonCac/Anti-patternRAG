import json
import os
from pathlib import Path
from typing import Union

from config.settings import MAX_CHUNK_CHARS, ANTIPATTERN_TYPE

max_chunk_chars = MAX_CHUNK_CHARS

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
    构建单个反模式案例的 chunk（仅包含 Java 文件内容）。
    对多个 Java 文件按 max_chunk_chars 均分内容限制。

    返回格式：{content: ..., metadata: {...}}
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
        _, project_name, commit_number, case_id = parts

    # 找到 JSON 文件（一个案例文件夹应该只有一个 *antipattern.json）
    json_files = list(base_dir.glob("*antipattern.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON name *antipattern.json file found in {base_dir}")

    json_path = json_files[0]
    with open(json_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    super_path = raw["files"][0]
    sub_path = raw["files"][1]

    # 解析 2 个 Java 文件路径, 构建 Java 文件的完整路径（from before/ 目录）
    java_base_dir = base_dir / "before"
    super_path = os.path.join(java_base_dir, super_path)
    sub_path = os.path.join(java_base_dir, sub_path)

    chunks = []
    chunks.append({
        "file_path": super_path,
        "chunk_type": "superClass",
        "ast_subtree": Path(super_path).read_text(encoding="utf-8")
    })
    chunks.append({
        "file_path": sub_path,
        "chunk_type": "subClass",
        "ast_subtree": Path(sub_path).read_text(encoding="utf-8")
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
        output_dir = Path(f"tmp_ablation/chunks/{antipattern_type}")
    output_dir.mkdir(parents=True, exist_ok=True)  # 自动创建目录
    output_path = output_dir / chunk_filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"分块结果已保存至: {output_path}")
    return result, output_path



def build_mh_chunks(base_dir: Union[str, Path], antipattern_type, group_id):
    return


def build_awd_chunks(base_dir: Union[str, Path], antipattern_type, group_id):
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
        raise FileNotFoundError(f"No JSON name *_awd_antipattern.json file found in {base_dir}")

    json_path = json_files[0]

    # 解析 2 个 Java 文件路径, 构建 Java 文件的完整路径（from before/ 目录）
    java_base_dir = base_dir / "before"

    with open(json_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    client_path = raw["files"][0]
    super_path = raw["files"][1]
    sub_path = raw["files"][2]
    client_path = os.path.join(java_base_dir, client_path)
    super_path = os.path.join(java_base_dir, super_path)
    sub_path = os.path.join(java_base_dir, sub_path)

    chunks = []
    chunks.append({
        "file_path": client_path,
        "chunk_type": "clientClass",
        "ast_subtree": Path(client_path).read_text(encoding="utf-8")
    })
    chunks.append({
        "file_path": super_path,
        "chunk_type": "superType",
        "ast_subtree": Path(super_path).read_text(encoding="utf-8")
    })
    chunks.append({
        "file_path": sub_path,
        "chunk_type": "subType",
        "ast_subtree": Path(sub_path).read_text(encoding="utf-8")
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
        output_dir = Path(f"tmp_ablation/chunks/{antipattern_type}")
    output_dir.mkdir(parents=True, exist_ok=True)  # 自动创建目录
    output_path = output_dir / chunk_filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"分块结果已保存至: {output_path}")
    return result, output_path