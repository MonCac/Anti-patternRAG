import os

from config.settings import MAX_CHUNK_CHARS, ANTIPATTERN_TYPE
from splitter.utils import read_limited_text

max_chunk_chars = MAX_CHUNK_CHARS
antipattern_type = ANTIPATTERN_TYPE


def build_chunk(case_path: str, case_id: str, max_chunk_chars: int = max_chunk_chars) -> dict:
    """
    构建单个反模式案例的 chunk（仅包含 Java 文件内容）。
    对多个 Java 文件按 max_chunk_chars 均分内容限制。

    返回格式：{content: ..., metadata: {...}}
    """
    before_path = os.path.join(case_path, 'before')
    java_files = []

    # 收集所有 Java 文件路径
    if os.path.isdir(before_path):
        for file_name in sorted(os.listdir(before_path)):
            if file_name.endswith(".java"):
                java_path = os.path.join(before_path, file_name)
                java_files.append((file_name, java_path))

    num_files = len(java_files)
    if num_files == 0:
        print(f"[WARN] No Java files found for case {case_id}")
        return {
            "content": f"Case ID: {case_id}\n[No Java files found]",
            "metadata": {
                "case_id": case_id,
                "antipattern_type": antipattern_type
            }
        }

    # 平均分配每个 Java 文件的最大字符数
    per_file_limit = max_chunk_chars // num_files

    # 构建 chunk 文本
    chunk_text = f"=== Anti-pattern Case ===\n"
    chunk_text += f"Case ID: {case_id}\n"
    chunk_text += f"Anti-pattern Type: {antipattern_type}\n\n"
    chunk_text += "--- Java Files ---\n"

    total_chars = len(chunk_text)

    for file_name, java_path in java_files:
        java_content = read_limited_text(java_path, max_chars=per_file_limit)

        chunk_text += f"[File: {file_name}]\n"
        chunk_text += java_content.strip() + "\n\n"

        total_chars = len(chunk_text)
        if total_chars >= max_chunk_chars:
            chunk_text = chunk_text[:max_chunk_chars] + "\n[Truncated due to length...]\n"
            break

    return {
        "content": chunk_text.strip(),
        "metadata": {
            "case_id": case_id,
            "antipattern_type": antipattern_type
        }
    }
