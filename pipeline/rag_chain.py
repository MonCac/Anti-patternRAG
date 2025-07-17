from langchain.schema import Document
from embeddings.vector_store import save_embeddings
from splitter.case_splitter import split_into_chunks
from embeddings.code_embedding import get_embedding_model, embed_chunk
from config.settings import DATA_DIR


def build_basic_rag_chain(query):
    data_dir = DATA_DIR
    # 1. 读取数据并分块
    docs = []
    print(f"data_dir: {data_dir}，DATA_DIR:{DATA_DIR}")
    chunks = split_into_chunks(data_dir)
    for i, chunk in enumerate(chunks):
        print(f"[{i}] {chunk}\n")
        docs.append(Document(page_content=chunk, metadata={"source_id": f"chunk_{i}"}))

    docs = [doc.page_content for doc in docs]
    # 2. 嵌入模型
    embed = get_embedding_model()
    # 循环使用 ollama 对单文本 embedding 的函数
    embeddings = [embed_chunk(embed, chunk) for chunk in docs]
    # 直接使用 ollama 内置对列表进行 embedding 的函数
    # embeddings = embed.embed_documents(docs)
    print("embeddings[0]: ", embeddings[0])
    print("len: embeddings: ", len(embeddings))
    print("len: embeddings[0]: ", len(embeddings[0]))

    # 3. 向量库（Chromadb）
    chromadb_collection = save_embeddings(docs, embeddings)
    # 4. 自定义检索器包装（方便后续扩展）
    query_embedding = embed_chunk(embed, query)
    results = chromadb_collection.query(
        query_embeddings=[query_embedding],
        n_results=4
    )
    result = results['documents'][0]

    for i, chunk in enumerate(result):
        print(f"[{i}] {chunk}\n")
