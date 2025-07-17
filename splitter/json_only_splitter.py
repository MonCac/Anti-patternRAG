import json
import os

from config.settings import MAX_CHUNK_CHARS, ANTIPATTERN_TYPE

max_chunk_chars = MAX_CHUNK_CHARS
antipattern_type = ANTIPATTERN_TYPE


def build_chunk(case_path: str, case_id: str, max_chunk_chars: int = max_chunk_chars) -> dict:
    """
    构建单个反模式案例的 chunk（仅包含 JSON 内容）。
    包括：
        - JSON 文件的原始字符串内容（做截断处理）
        - 必要的标识信息（如 case_id, antipattern_type）

    返回格式：{content: ..., metadata: {...}}
    """
    # 获取 JSON 文件路径
    json_file = next((f for f in os.listdir(case_path) if f.endswith('_antipattern.json')), None)

    json_data = {}
    json_content = ""

    # 解析 JSON 内容
    if json_file:
        try:
            with open(os.path.join(case_path, json_file), 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                json_content = json.dumps(json_data, indent=2)
        except Exception as e:
            print(f"[ERROR] Failed to parse JSON for {case_id}: {e}")

    # 构建 chunk 文本，仅包含 JSON 内容
    chunk_text = f"=== Anti-pattern Case ===\n"
    chunk_text += f"Case ID: {case_id}\n"
    chunk_text += f"Anti-pattern Type: {antipattern_type}\n\n"
    chunk_text += "--- Anti-pattern JSON ---\n"

    # 添加截断处理
    chunk_text += json_content[:max_chunk_chars]
    if len(json_content) > max_chunk_chars:
        chunk_text += "\n[Truncated due to length...]\n"

    return {
        "content": chunk_text.strip(),
        "metadata": {
            "case_id": case_id,
            "antipattern_type": antipattern_type
        }
    }
