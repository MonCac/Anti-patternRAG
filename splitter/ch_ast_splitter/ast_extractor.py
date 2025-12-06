import os
import warnings

from tree_sitter import Language, Parser
from typing import Optional

from splitter.ch_ast_splitter.ast_chunk_schema import ASTChunk
from splitter.ch_ast_splitter.base_chunk_schema import ChunkType, AWDChunkType

warnings.filterwarnings("ignore", category=FutureWarning)

print("Current working directory:", os.getcwd())

# 初始化 Java parser
JAVA_LANGUAGE = Language('build/my-languages.so', 'java')
parser = Parser()
parser.set_language(JAVA_LANGUAGE)


def read_source_file(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_node_by_line_range(root_node, start_line: int, end_line: int):
    """
    找到覆盖从 start_line 到 end_line 的最小节点，节点必须完全覆盖区间。
    """
    candidates = []

    def traverse(node):
        node_start = node.start_point[0] + 1
        node_end = node.end_point[0] + 1

        # 只考虑完全覆盖区间的节点
        if node_start <= start_line and node_end >= end_line:
            candidates.append(node)
            for child in node.children:
                traverse(child)

    traverse(root_node)
    if not candidates:
        return None
    # 返回跨度最小的节点
    return min(candidates, key=lambda n: (n.end_point[0] - n.start_point[0]))


def extract_ast_chunk(code: str, file_path: str, chunk_type,
                      start_line: Optional[int] = None, end_line: Optional[int] = None) -> ASTChunk:
    tree = parser.parse(bytes(code, "utf8"))
    root_node = tree.root_node

    if start_line and end_line:
        node = get_node_by_line_range(root_node, start_line, end_line)
    else:
        node = root_node

    return ASTChunk(
        file_path=file_path,
        chunk_type=chunk_type,
        level=3,
        chunk_id=chunk_type.value,
        ast_subtree=node.sexp()  # 使用 S-expression 结构作为语法表示
    )


def extract_superclass_chunks(code: str, file_path: str,
                              parent_loc: Optional[tuple] = None,
                              invocation_loc: Optional[tuple] = None) -> list[ASTChunk]:
    chunks = []
    if parent_loc:
        start_line, end_line = parent_loc
        chunks.append(
            extract_ast_chunk(code, file_path, ChunkType.PARENT_METHOD, start_line, end_line)
        )

    if invocation_loc:
        start_line, end_line = invocation_loc
        chunks.append(
            extract_ast_chunk(code, file_path, ChunkType.PARENT_CALL_CHILD, start_line, end_line)
        )
    # 整体结构
    chunks.append(
        extract_ast_chunk(code, file_path, ChunkType.PARENT_FILE_STRUCTURE)
    )
    return chunks


def extract_subclass_chunks(code: str, file_path: str,
                            method_loc: Optional[tuple] = None) -> list[ASTChunk]:
    chunks = []
    if method_loc:
        start_line, end_line = method_loc
        chunks.append(
            extract_ast_chunk(code, file_path, ChunkType.CHILD_METHOD, start_line, end_line)
        )
    # 整体结构
    chunks.append(
        extract_ast_chunk(code, file_path, ChunkType.CHILD_FILE_STRUCTURE)
    )
    return chunks


def extract_awd_superclass_chunks(super_code, super_path, client_code, client_path, superType_parent_method_loc,
                                  superType_child_method_loc, superType_invocation_loc):
    chunks = []
    if superType_parent_method_loc:
        start_line, end_line = superType_parent_method_loc
        chunks.append(
            extract_ast_chunk(client_code, client_path, AWDChunkType.SUPER_PARENT_METHOD, start_line, end_line)
        )

    if superType_child_method_loc:
        start_line, end_line = superType_child_method_loc
        chunks.append(
            extract_ast_chunk(super_code, super_path, AWDChunkType.SUPER_CHILD_METHOD, start_line, end_line)
        )

    if superType_invocation_loc:
        start_line, end_line = superType_invocation_loc
        chunks.append(
            extract_ast_chunk(client_code, client_path, AWDChunkType.SUPER_INVOCATION, start_line, end_line)
        )

    return chunks


def extract_awd_subclass_chunks(sub_code, sub_path, client_code, client_path, subType_parent_method_loc,
                                  subType_child_method_loc, subType_invocation_loc):
    chunks = []
    if subType_parent_method_loc:
        start_line, end_line = subType_parent_method_loc
        chunks.append(
            extract_ast_chunk(client_code, client_path, AWDChunkType.SUB_PARENT_METHOD, start_line, end_line)
        )

    if subType_child_method_loc:
        start_line, end_line = subType_child_method_loc
        chunks.append(
            extract_ast_chunk(sub_code, sub_path, AWDChunkType.SUB_CHILD_METHOD, start_line, end_line)
        )

    if subType_invocation_loc:
        start_line, end_line = subType_invocation_loc
        chunks.append(
            extract_ast_chunk(client_code, client_path, AWDChunkType.SUB_INVOCATION, start_line, end_line)
        )

    return chunks
