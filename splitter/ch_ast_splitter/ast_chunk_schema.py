from dataclasses import dataclass
from splitter.ch_ast_splitter.base_chunk import BaseChunk


@dataclass
class ASTChunk(BaseChunk):
    ast_subtree: str
