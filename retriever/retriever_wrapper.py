from langchain.schema import BaseRetriever


class MyRetriever(BaseRetriever):
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore

    def get_relevant_documents(self, query):
        # 这里直接调用底层向量库的相似度检索
        return self.vectorstore.similarity_search(query)

