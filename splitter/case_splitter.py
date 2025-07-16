from typing import List


def simple_text_splitter(text, chunk_size=50):
    """最简单的分块器，按字符数切分"""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]


# 读取文档，并对文档按照 "\n\n" 进行分块
def split_into_chunks(doc_file: str) -> List[str]:
    with open(doc_file, 'r') as file:
        content = file.read()
    return [chunk for chunk in content.split("\n\n")]