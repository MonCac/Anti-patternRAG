from dataclasses import dataclass
from splitter.ch_ast_splitter.base_chunk_schema import BaseChunk


@dataclass
class ASTChunk(BaseChunk):
    ast_subtree: str = ""

