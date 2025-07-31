from pathlib import Path

from config.settings import DATA_DIR
from pipeline.rag_chain import build_basic_rag_chain
from prompts.prompt_loader import load_prompt
from splitter.ch_ast_splitter.ast_case_splitter import split_ch_case_into_chunks


def main():
    print("[RAG Demo] 输入 exit 退出")
    while True:
        sum = 4
        question = load_prompt("example").format(sum=sum)
        query = input(question)
        if query.lower() in ("exit", "quit"):
            break
        result = build_basic_rag_chain(query)
        print("\n===== RAG回答 =====")
        print(result)


if __name__ == "__main__":
    # main()
    split_ch_case_into_chunks(Path(DATA_DIR) / "kafka" / "commit_1000" / "6", 0)
