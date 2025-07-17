def read_limited_text(file_path: str, max_chars: int) -> str:
    """
    读取文件内容，最多读取 max_chars 个字符。
    用于防止单个 Java 文件内容过长。
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        return content[:max_chars] if len(content) > max_chars else content