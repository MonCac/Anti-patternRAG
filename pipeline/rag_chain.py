from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import Document
from splitter.case_splitter import simple_text_splitter, split_into_chunks
from embeddings.code_embedding import get_embedding_model
from retriever.retriever_wrapper import MyRetriever


def build_basic_rag_chain():

    # 1. 读取数据并分块
    docs = []
    chunks = split_into_chunks("/Users/moncheri/Downloads/main/重构/反模式修复数据集构建/RefactorRAG/Anti-PatternRAG/data/doc.md")
    for i, chunk in enumerate(chunks):
        print(f"[{i}] {chunk}\n")
        docs.append(Document(page_content=chunk, metadata={"source_id": f"chunk_{i}"}))

    # 2. 嵌入模型
    embedding_model = get_embedding_model()

    # 3. 向量库（FAISS）
    vectorstore = FAISS.from_documents(docs, embedding_model)

    # 4. 自定义检索器包装（方便后续扩展）
    retriever = MyRetriever(vectorstore)

    # 5. LLM
    llm = ChatOpenAI(temperature=0)

    # 6. RAG Chain
    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )

    return rag_chain
