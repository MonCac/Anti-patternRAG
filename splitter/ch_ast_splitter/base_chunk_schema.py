from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Union


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


class AWDChunkType(Enum):
    SUPER_PARENT_METHOD = "super_parent_method"
    SUPER_CHILD_METHOD = "super_child_method"
    SUPER_INVOCATION = "super_invocation"
    SUB_PARENT_METHOD = "sub_parent_method"
    SUB_CHILD_METHOD = "sub_child_method"
    SUB_INVOCATION = "sub_invocation"
    CLIENT_SUMMARY = "client_summary"
    SUPER_SUMMARY = "super_summary"
    SUB_SUMMARY = "sub_summary"

@dataclass
class BaseChunk:
    file_path: str
    chunk_type: Union[ChunkType, AWDChunkType]
    chunk_id: str
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
