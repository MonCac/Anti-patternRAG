from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional


class ChunkType(Enum):
    PARENT_METHOD = "parent_method"
    PARENT_CALL_CHILD = "parent_call_child"
    CHILD_METHOD = "child_method"
    PARENT_FILE_STRUCTURE = "parent_file_structure"
    CHILD_FILE_STRUCTURE = "child_file_structure"
    PARENT_FILE_SUMMARY = "parent_file_summary"
    PARENT_METHOD_SUMMARY = "parent_method_summary"
    INVOCATION_SUMMARY = "invocation_summary"
    CHILD_FILE_SUMMARY = "child_file_summary"
    CHILD_METHOD_SUMMARY = "child_method_summary"


@dataclass
class BaseChunk:
    file_path: str
    chunk_type: ChunkType
    chunk_id: str
    group_id: int
    level: int
    parent_chunk_id: Optional[str] = None

    def to_dict(self):
        result = {}
        for k, v in asdict(self).items():
            if isinstance(v, Enum):
                result[k] = v.value
            else:
                result[k] = v
        return result
