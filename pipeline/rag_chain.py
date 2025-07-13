from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import Document
from splitter.case_splitter import simple_text_splitter
from embeddings.code_embedding import get_embedding_model
from retriever.retriever_wrapper import MyRetriever

def build_basic_rag_chain():
    # 1. 模拟读取数据，后续改为读取 data/raw
    raw_texts = [
        "Memory leak occurs because file handles are not closed.",
        "Hardcoded credentials in source code can cause security issues."
    ]

    # 2. 分块
    docs = []
    for i, text in enumerate(raw_texts):
        chunks = simple_text_splitter(text)
        for j, chunk in enumerate(chunks):
            docs.append(Document(page_content=chunk, metadata={"source_id": f"case_{i}_chunk_{j}"}))

    # 3. 嵌入模型
    embedding_model = get_embedding_model()

    # 4. 向量库（FAISS）
    vectorstore = FAISS.from_documents(docs, embedding_model)

    # 5. 自定义检索器包装（方便后续扩展）
    retriever = MyRetriever(vectorstore)

    # 6. LLM
    llm = ChatOpenAI(temperature=0)

    # 7. RAG Chain
    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )

    return rag_chain
