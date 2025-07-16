from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="llama3")
print(llm.invoke("你好"))
