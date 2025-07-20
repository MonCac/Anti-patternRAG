from utils.utils import read_code_from_file
from .base_chunk import ChunkType
from .llm_chunk_schema import LLMChunk
from llm.llm_client import run_llm
from prompts.prompt_loader import load_prompt


def llm_analyze_superclass(file_path: str, method_code: str, invocation_code: str) -> list[LLMChunk]:
    full_code = read_code_from_file(file_path)

    parent_file_prompt = load_prompt("parent_file_prompt")
    parent_method_prompt = load_prompt("parent_method_prompt")
    invocation_prompt = load_prompt("invocation_prompt")

    return [
        LLMChunk(file_path, ChunkType.PARENT_FILE_SUMMARY, run_llm(parent_file_prompt, {"code": full_code})),
        LLMChunk(file_path, ChunkType.PARENT_METHOD_SUMMARY, run_llm(parent_method_prompt, {"code": method_code})),
        LLMChunk(file_path, ChunkType.INVOCATION_SUMMARY, run_llm(invocation_prompt, {"code": invocation_code}))
    ]


def llm_analyze_subclass(file_path: str, method_code: str) -> list[LLMChunk]:
    full_code = read_code_from_file(file_path)

    child_file_prompt = load_prompt("child_file_prompt")
    child_method_prompt = load_prompt("child_method_prompt")

    return [
        LLMChunk(file_path, ChunkType.CHILD_FILE_SUMMARY, run_llm(child_file_prompt, {"code": full_code})),
        LLMChunk(file_path, ChunkType.CHILD_METHOD_SUMMARY, run_llm(child_method_prompt, {"code": method_code}))
    ]
