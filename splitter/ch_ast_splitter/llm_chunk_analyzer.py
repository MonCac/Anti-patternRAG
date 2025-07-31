from utils.utils import read_code_from_file
from .base_chunk_schema import ChunkType
from .llm_chunk_schema import LLMChunk
from llm.llm_client import run_llm
from prompts.prompt_loader import load_prompt, split_prompt


def llm_analyze_superclass(file_path: str, method_code: str, group_id: int, invocation_code: str) -> list[LLMChunk]:
    full_code = read_code_from_file(file_path)

    parent_file_prompt = load_prompt("parent_file_prompt")
    parent_file_system_prompt, parent_file_user_prompt = split_prompt(parent_file_prompt)
    parent_method_prompt = load_prompt("parent_method_prompt")
    parent_method_system_prompt, parent_method_user_prompt = split_prompt(parent_method_prompt)
    invocation_prompt = load_prompt("invocation_prompt")
    invocation_system_prompt, invocation_user_prompt = split_prompt(invocation_prompt)

    return [
        LLMChunk(file_path=file_path,
                 chunk_type=ChunkType.PARENT_FILE_SUMMARY,
                 group_id=group_id,
                 level=3,
                 chunk_id=ChunkType.PARENT_FILE_SUMMARY.value,
                 llm_description=run_llm(parent_file_system_prompt, parent_file_user_prompt, {"code": full_code})
                 ),
        LLMChunk(file_path=file_path,
                 chunk_type=ChunkType.PARENT_METHOD_SUMMARY,
                 group_id=group_id,
                 level=3,
                 chunk_id=ChunkType.PARENT_METHOD_SUMMARY.value,
                 llm_description=run_llm(parent_method_system_prompt, parent_method_user_prompt, {"code": method_code})
                 ),
        LLMChunk(file_path=file_path,
                 chunk_type=ChunkType.INVOCATION_SUMMARY,
                 group_id=group_id,
                 level=3,
                 chunk_id=ChunkType.INVOCATION_SUMMARY.value,
                 llm_description=run_llm(invocation_system_prompt, invocation_user_prompt, {"code": invocation_code})
                 ),
    ]


def llm_analyze_subclass(file_path: str, group_id: int, method_code: str) -> list[LLMChunk]:
    full_code = read_code_from_file(file_path)

    child_file_prompt = load_prompt("child_file_prompt")
    child_file_system_prompt, child_file_user_prompt = split_prompt(child_file_prompt)
    child_method_prompt = load_prompt("child_method_prompt")
    child_method_system_prompt, child_method_user_prompt = split_prompt(child_method_prompt)

    return [
        LLMChunk(file_path=file_path,
                 chunk_type=ChunkType.CHILD_FILE_SUMMARY,
                 group_id=group_id,
                 level=3,
                 chunk_id=ChunkType.CHILD_FILE_SUMMARY.value,
                 llm_description=run_llm(child_file_system_prompt, child_file_user_prompt, {"code": full_code})
                 ),
        LLMChunk(file_path=file_path,
                 chunk_type=ChunkType.CHILD_METHOD_SUMMARY,
                 group_id=group_id,
                 level=3,
                 chunk_id=ChunkType.CHILD_METHOD_SUMMARY.value,
                 llm_description=run_llm(child_method_system_prompt, child_method_user_prompt, {"code": method_code})
                 ),
    ]
