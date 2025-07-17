from pipeline.rag_chain import build_basic_rag_chain
from prompts.prompt_loader import load_prompt


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
    main()
