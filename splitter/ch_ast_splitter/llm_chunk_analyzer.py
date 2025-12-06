from pathlib import Path

from utils.utils import read_code_from_file
from .base_chunk_schema import ChunkType, AWDChunkType
from .llm_chunk_schema import LLMChunk
from llm.llm_client import run_llm
from prompts.prompt_loader import load_prompt, split_prompt


def llm_analyze_superclass(file_path: str, method_code: str, invocation_code: str) -> list[LLMChunk]:
    full_code = read_code_from_file(file_path)

    parent_file_prompt = load_prompt("chunk_prompts/parent_file_prompt")
    parent_file_system_prompt, parent_file_user_prompt = split_prompt(parent_file_prompt)
    parent_method_prompt = load_prompt("chunk_prompts/parent_method_prompt")
    parent_method_system_prompt, parent_method_user_prompt = split_prompt(parent_method_prompt)
    invocation_prompt = load_prompt("chunk_prompts/invocation_prompt")
    invocation_system_prompt, invocation_user_prompt = split_prompt(invocation_prompt)

    return [
        LLMChunk(file_path=file_path,
                 chunk_type=ChunkType.PARENT_FILE_SUMMARY,
                 level=3,
                 chunk_id=ChunkType.PARENT_FILE_SUMMARY.value,
                 llm_description=run_llm(parent_file_system_prompt, parent_file_user_prompt, {"code": full_code})
                 ),
        LLMChunk(file_path=file_path,
                 chunk_type=ChunkType.PARENT_METHOD_SUMMARY,
                 level=3,
                 chunk_id=ChunkType.PARENT_METHOD_SUMMARY.value,
                 llm_description=run_llm(parent_method_system_prompt, parent_method_user_prompt, {"code": method_code})
                 ),
        LLMChunk(file_path=file_path,
                 chunk_type=ChunkType.INVOCATION_SUMMARY,
                 level=3,
                 chunk_id=ChunkType.INVOCATION_SUMMARY.value,
                 llm_description=run_llm(invocation_system_prompt, invocation_user_prompt, {"code": invocation_code})
                 ),
    ]


def llm_analyze_subclass(file_path: str, method_code: str) -> list[LLMChunk]:
    full_code = read_code_from_file(file_path)

    child_file_prompt = load_prompt("chunk_prompts/child_file_prompt")
    child_file_system_prompt, child_file_user_prompt = split_prompt(child_file_prompt)
    child_method_prompt = load_prompt("chunk_prompts/child_method_prompt")
    child_method_system_prompt, child_method_user_prompt = split_prompt(child_method_prompt)

    return [
        LLMChunk(file_path=file_path,
                 chunk_type=ChunkType.CHILD_FILE_SUMMARY,
                 level=3,
                 chunk_id=ChunkType.CHILD_FILE_SUMMARY.value,
                 llm_description=run_llm(child_file_system_prompt, child_file_user_prompt, {"code": full_code})
                 ),
        LLMChunk(file_path=file_path,
                 chunk_type=ChunkType.CHILD_METHOD_SUMMARY,
                 level=3,
                 chunk_id=ChunkType.CHILD_METHOD_SUMMARY.value,
                 llm_description=run_llm(child_method_system_prompt, child_method_user_prompt, {"code": method_code})
                 ),
    ]


def awd_llm_analyze_subclass(client_path, super_path, sub_path, llm_before_content):
    client_desc, super_desc, sub_desc = get_llm_descriptions_by_suffix_path(client_path, super_path, sub_path, llm_before_content)

    return [
        LLMChunk(file_path=client_path,
                 chunk_type=AWDChunkType.CLIENT_SUMMARY,
                 level=3,
                 chunk_id=AWDChunkType.CLIENT_SUMMARY.value,
                 llm_description=client_desc
                 ),
        LLMChunk(file_path=super_path,
                 chunk_type=AWDChunkType.SUPER_SUMMARY,
                 level=3,
                 chunk_id=AWDChunkType.SUPER_SUMMARY.value,
                 llm_description=super_desc
                 ),
        LLMChunk(file_path=sub_path,
                 chunk_type=AWDChunkType.SUB_SUMMARY,
                 level=3,
                 chunk_id=AWDChunkType.SUB_SUMMARY.value,
                 llm_description=sub_desc
                 )
    ]


def match_by_suffix_path(abs_path: str, rel_path: str) -> bool:
    """
    判断绝对路径的最后N级目录是否等于相对路径（N是相对路径的部分数）
    """
    abs_p = Path(abs_path)
    rel_p = Path(rel_path)
    n = len(rel_p.parts)
    # 取绝对路径的后n部分
    abs_suffix = abs_p.parts[-n:]
    return abs_suffix == rel_p.parts


def get_llm_descriptions_by_suffix_path(client_rel_path, super_rel_path, sub_rel_path, llm_before_content):
    def find_desc_by_rel_path(rel_path):
        for info in llm_before_content.values():
            abs_path = info.get("file_path", "")
            if match_by_suffix_path(abs_path, rel_path):
                return info.get("function_description", "")
        return ""

    client_desc = find_desc_by_rel_path(client_rel_path)
    super_desc = find_desc_by_rel_path(super_rel_path)
    sub_desc = find_desc_by_rel_path(sub_rel_path)

    return client_desc, super_desc, sub_desc
