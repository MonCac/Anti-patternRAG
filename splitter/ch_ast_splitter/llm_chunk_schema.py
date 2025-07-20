from dataclasses import dataclass

from splitter.ch_ast_splitter.base_chunk import BaseChunk


@dataclass
class LLMChunk(BaseChunk):
    llm_description: str  # 实际是自然语言描述
