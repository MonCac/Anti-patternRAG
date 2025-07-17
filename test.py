from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="gemma3:1b")
print(llm.invoke("你好"))
