from pathlib import Path
import json
from typing import Dict, List, Any, Union
from dataclasses import dataclass


@dataclass
class MethodLocation:
    entity: str
    location: str
    code: str

@dataclass
class InvocationLocation:
    location: str
    code: str


@dataclass
class CodeSnippet:
    from_file: str
    to_file: str
    relation_type: str
    parent_method: MethodLocation
    child_method: MethodLocation
    invocation: InvocationLocation


@dataclass
class CaseInfo:
    super_class_path: str
    sub_class_path: str
    code_snippets: List[CodeSnippet]
    raw_json: Dict[str, Any]
    case_id: str


def load_case_info(json_path: Union[str, Path]) -> CaseInfo:
    with open(json_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    super_path = raw["files"][0]
    sub_path = raw["files"][1]
    snippets = []

    for snip in raw.get("codeSnippets", []):
        snippets.append(CodeSnippet(
            from_file=snip["fromFile"],
            to_file=snip["toFile"],
            relation_type=snip["relationType"],
            parent_method=MethodLocation(**snip["parentMethod"]),
            child_method=MethodLocation(**snip["childMethod"]),
            invocation=InvocationLocation(**snip["invocation"])
        ))

    return CaseInfo(
        super_class_path=super_path,
        sub_class_path=sub_path,
        code_snippets=snippets,
        raw_json=raw,
        case_id=json_path.stem
    )
