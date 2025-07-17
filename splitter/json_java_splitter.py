import json
import os

from config.settings import MAX_CHUNK_CHARS, ANTIPATTERN_TYPE
from splitter.utils import read_limited_text

max_chunk_chars = MAX_CHUNK_CHARS
antipattern_type = ANTIPATTERN_TYPE


def build_chunk(case_path: str, case_id: str, max_chunk_chars: int = max_chunk_chars) -> dict:
    """
    构建单个反模式案例的 chunk（json + java 分块方式）：
    - 优先写入 JSON 文件内容（完整写入，若超长则截断）
    - 剩余字符预算均分给所有 Java 文件内容（before 文件夹下）

    返回：{ "content": str, "metadata": dict }
    """
    before_path = os.path.join(case_path, 'before')
    java_files = []

    # 收集 Java 文件路径
    if os.path.isdir(before_path):
        for file_name in sorted(os.listdir(before_path)):
            if file_name.endswith(".java"):
                java_path = os.path.join(before_path, file_name)
                java_files.append((file_name, java_path))

    # 处理 JSON 文件内容
    json_content = ""
    json_file = next((f for f in os.listdir(case_path) if f.endswith('_antipattern.json')), None)

    if json_file:
        try:
            with open(os.path.join(case_path, json_file), 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                json_content = json.dumps(json_data, indent=2)
        except Exception as e:
            print(f"[ERROR] Failed to parse JSON for {case_id}: {e}")
            json_content = "[ERROR] JSON parsing failed."

    # 初始化 chunk 内容
    chunk_text = f"=== Anti-pattern Case ===\n"
    chunk_text += f"Case ID: {case_id}\n"
    chunk_text += f"Anti-pattern Type: {antipattern_type}\n\n"
    chunk_text += "--- Anti-pattern JSON ---\n"
    chunk_text += json_content.strip() + "\n\n"

    # 计算剩余字符预算
    remaining_chars = max_chunk_chars - len(chunk_text)
    if remaining_chars > 0 and java_files:
        chunk_text += "--- Java Files ---\n"
        per_file_limit = remaining_chars // len(java_files)

        for file_name, java_path in java_files:
            java_content = read_limited_text(java_path, max_chars=per_file_limit)
            chunk_text += f"[File: {file_name}]\n"
            chunk_text += java_content.strip() + "\n\n"

    return {
        "content": chunk_text.strip(),
        "metadata": {
            "case_id": case_id,
            "antipattern_type": antipattern_type
        }
    }
