from langchain_ollama import OllamaEmbeddings


def get_embedding_model():
    # 简单封装，后续可改成 CodeBERT/CodeT5 等模型
    return OpenAIEmbeddings()
