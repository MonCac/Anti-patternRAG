from dataclasses import dataclass
from enum import Enum


class LLMChunkType(Enum):
    PARENT_FILE_SUMMARY = "parent_file_summary"
    PARENT_METHOD_SUMMARY = "parent_method_summary"
    INVOCATION_SUMMARY = "invocation_summary"
    CHILD_FILE_SUMMARY = "child_file_summary"
    CHILD_METHOD_SUMMARY = "child_method_summary"


@dataclass
class LLMChunk:
    file_path: str
    chunk_type: LLMChunkType
    llm_description: str  # 实际是自然语言描述
