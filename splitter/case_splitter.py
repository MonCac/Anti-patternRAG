def simple_text_splitter(text, chunk_size=50):
    """最简单的分块器，按字符数切分"""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]