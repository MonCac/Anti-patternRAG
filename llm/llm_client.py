import time

from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.settings import LLM_MODEL

parser = StrOutputParser()


def run_llm(system_prompt_template: str, user_prompt_template: str, variables: dict) -> str:
    """
    通用大模型调用接口，支持失败重试 + 运行时间统计。
    """
    print("talk with llm")

    start_time = time.perf_counter()

    prompt = PromptTemplate.from_template(user_prompt_template)
    llm = ChatOllama(model=LLM_MODEL, system=system_prompt_template)

    chain = prompt | llm | parser

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            output = chain.invoke(variables)
            print(f"LLM output: {output}")
            break
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                raise
            time.sleep(1)

    elapsed = time.perf_counter() - start_time
    print(f"run_llm elapsed time: {elapsed:.3f}s")

    return output
