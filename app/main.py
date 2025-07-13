from pipeline.rag_chain import build_basic_rag_chain

def main():
    chain = build_basic_rag_chain()
    print("[RAG Demo] 输入 exit 退出")
    while True:
        query = input("\n请输入查询内容：")
        if query.lower() in ("exit", "quit"):
            break
        result = chain.run(query)
        print("\n===== RAG回答 =====")
        print(result)

if __name__ == "__main__":
    main()
