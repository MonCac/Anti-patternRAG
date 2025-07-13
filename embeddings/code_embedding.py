from langchain_community.embeddings import OpenAIEmbeddings


def get_embedding_model():
    # 简单封装，后续可改成 CodeBERT/CodeT5 等模型
    return OpenAIEmbeddings()
