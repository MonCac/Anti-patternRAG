from dataclasses import dataclass
from enum import Enum


class ChunkType(Enum):
    PARENT_METHOD = "parent_method"
    PARENT_CALL_CHILD = "parent_call_child"
    CHILD_METHOD = "child_method"
    PARENT_FILE_STRUCTURE = "parent_file_structure"
    CHILD_FILE_STRUCTURE = "child_file_structure"
    PARENT_FILE_SUMMARY = "parent_file_summary"
    PARENT_METHOD_SUMMARY = "parent_method_summary"
    INVOCATION_SUMMARY = "invocation_summary"


@dataclass
class BaseChunk:
    file_path: str
    chunk_type: ChunkType
    content: str
