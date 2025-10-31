from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.settings import LLM_MODEL

parser = StrOutputParser()


def run_llm(system_prompt_template: str, user_prompt_template: str, variables: dict) -> str:
    """
    通用大模型调用接口。
    """
    print("talk with llm")
    prompt = PromptTemplate.from_template(user_prompt_template)
    llm = ChatOllama(model=LLM_MODEL, system=system_prompt_template)

    chain = prompt | llm | parser
    print(f"system prompt: {system_prompt_template}")
    print(f"user prompt: {user_prompt_template}")
    output = chain.invoke(variables)
    print(f"LLM output : {output}")
    return output
