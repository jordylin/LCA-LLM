#!/usr/bin/env python3
"""
OpenAI proprietary baseline with the same tool semantics as EcoLLM.

Design goal
1. Reuse the existing SHORT_E test dialogues in test_data/short_extract.
2. Keep the task definition and tool semantics close to EcoLLM.
3. Use an OpenAI API model instead of the local Qwen/vLLM stack.
4. Run a lightweight tool loop driven by the model.
5. Produce a prediction file compatible with the current evaluation pipeline.

Important note
The current SHORT_E assets are dialogue-based evaluation files with embedded
evidence chunks, not raw-PDF-only test cases. Therefore this baseline uses
dialogue-derived evidence as the document corpus for search_document. This
keeps the test set aligned with the current repository assets while still
testing proprietary tool-calling behavior.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import string
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_API_BASE = "https://api.openai.com/v1"
DEFAULT_TEST_DIR = "test_data/short_extract"
DEFAULT_OUTPUT = "results/openai_tools_baseline/predictions.json"
DEFAULT_TOP_K = 5

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "for", "in", "on", "with", "this",
    "that", "these", "those", "i", "you", "we", "they", "it", "is", "are", "was",
    "were", "be", "as", "by", "from", "at", "into", "during", "used", "use",
    "need", "record", "extract", "document", "data", "main", "step", "life",
    "cycle", "inventory", "please", "help", "me", "can", "could", "would",
}

ALLOWED_CATEGORIES = [
    "Raw Material",
    "Process Energy",
    "Post-processing Energy",
    "Feedstock Energy",
    "Gas",
    "Cooling Media",
    "Product",
    "Recovered Material",
    "Waste",
    "Emission",
]

CATEGORY_ALIASES = {
    "energy": "Process Energy",
    "electricity": "Process Energy",
    "material": "Raw Material",
    "raw material": "Raw Material",
    "feedstock": "Raw Material",
    "feedstock energy": "Feedstock Energy",
    "gas": "Gas",
    "cooling water": "Cooling Media",
    "cooling media": "Cooling Media",
    "product": "Product",
    "recovered material": "Recovered Material",
    "waste": "Waste",
    "emission": "Emission",
}


@dataclass
class Chunk:
    chunk_id: str
    content: str
    source: str


@dataclass
class SessionState:
    session_id: str
    chunks: List[Chunk]
    records: List[Dict[str, Any]] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    scopes: List[Dict[str, Any]] = field(default_factory=list)
    calculations: List[Dict[str, Any]] = field(default_factory=list)
    action_counter: int = 0

    def next_action_id(self) -> str:
        self.action_counter += 1
        return f"ACT_{self.action_counter:04d}"


def normalize_text(text: str) -> str:
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> List[str]:
    norm = normalize_text(text)
    return [tok for tok in norm.split() if tok and tok not in STOPWORDS]


def extract_json_from_tool_response(content: str) -> Dict[str, Any] | None:
    if not content:
        return None
    stripped = content.strip()
    stripped = re.sub(r"^<tool_response>\s*", "", stripped)
    stripped = re.sub(r"\s*</tool_response>$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None


def extract_preview_chunks(system_content: str) -> List[Chunk]:
    chunks: List[Chunk] = []
    pattern = re.compile(r"\*\*CHUNK\s+(\d+)\s+PREVIEW.*?\*\*:\s*\"(.*?)\"", re.DOTALL)
    for match in pattern.finditer(system_content or ""):
        chunk_id = match.group(1)
        content = match.group(2).strip()
        if content:
            chunks.append(Chunk(chunk_id=f"preview_{chunk_id}", content=content, source="system_preview"))
    return chunks


def deduplicate_chunks(chunks: List[Chunk]) -> List[Chunk]:
    seen: set[Tuple[str, str]] = set()
    unique: List[Chunk] = []
    for chunk in chunks:
        key = (chunk.chunk_id, normalize_text(chunk.content))
        if key in seen:
            continue
        seen.add(key)
        unique.append(chunk)
    return unique


def extract_chunks_from_messages(messages: List[Dict[str, Any]]) -> List[Chunk]:
    chunks: List[Chunk] = []

    for msg in messages:
        if msg.get("role") == "system":
            chunks.extend(extract_preview_chunks(msg.get("content", "")))

    for msg in messages:
        if msg.get("role") != "tool":
            continue
        payload = extract_json_from_tool_response(msg.get("content", ""))
        if not payload:
            continue
        for item in payload.get("results", []):
            chunk_id = str(item.get("chunk_id", "unknown"))
            content = (item.get("content") or "").strip()
            if content:
                chunks.append(Chunk(chunk_id=chunk_id, content=content, source="tool_search"))

    return deduplicate_chunks(chunks)


def lexical_score(query: str, chunk_text: str) -> float:
    q_tokens = tokenize(query)
    c_tokens = tokenize(chunk_text)
    if not q_tokens or not c_tokens:
        return 0.0

    q_set = set(q_tokens)
    c_set = set(c_tokens)
    overlap = q_set & c_set
    overlap_score = len(overlap) / max(len(q_set), 1)
    has_number = 1.0 if re.search(r"\d", chunk_text) else 0.0
    has_table = 1.0 if "|---|" in chunk_text or "## table" in chunk_text.lower() else 0.0
    return overlap_score + 0.15 * has_number + 0.1 * has_table


def retrieve_top_k(query: str, chunks: List[Chunk], top_k: int) -> List[Chunk]:
    scored = [(chunk, lexical_score(query, chunk.content)) for chunk in chunks]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [chunk for chunk, score in scored[:top_k] if score > 0]


def extract_user_request(messages: List[Dict[str, Any]]) -> str:
    for msg in messages:
        if msg.get("role") == "user":
            return (msg.get("content") or "").strip()
    return ""


def normalize_unit_and_value(value: float, unit: str) -> Tuple[float, str]:
    u = unit.strip().lower()
    if u in {"g", "gram", "grams"}:
        return value / 1000.0, "kg"
    if u in {"kg", "kilogram", "kilograms"}:
        return value, "kg"
    if u in {"kwh"}:
        return value, "kWh"
    if u in {"m3", "m^3", "m³"}:
        return value, "m³"
    if u in {"l", "liter", "liters", "litre", "litres"}:
        return value, "L"
    return value, unit


def normalize_category(category: str, flow_name: str) -> str:
    cat = category.strip()
    if cat in ALLOWED_CATEGORIES:
        return cat

    lowered = cat.lower()
    if lowered in CATEGORY_ALIASES:
        mapped = CATEGORY_ALIASES[lowered]
        if mapped == "Process Energy":
            name_low = flow_name.lower()
            if "powder production" in name_low or "feedstock" in name_low or "atomization" in name_low:
                return "Feedstock Energy"
        return mapped

    name_low = flow_name.lower()
    if "electric" in name_low or "power" in name_low or "energy" in name_low:
        if "powder production" in name_low or "atomization" in name_low or "feedstock" in name_low:
            return "Feedstock Energy"
        return "Process Energy"
    if "argon" in name_low or "nitrogen" in name_low or "air" in name_low or "gas" in name_low:
        return "Gas"
    if "water" in name_low and ("cool" in name_low or "cooling" in name_low):
        return "Cooling Media"
    if "product" in name_low or "rocker arm" in name_low or "part" in name_low:
        return "Product"
    if "powder" in name_low and ("spent" in name_low or "recovered" in name_low or "unused" in name_low):
        return "Recovered Material"
    if "powder" in name_low or "steel" in name_low or "alsi10mg" in name_low:
        return "Raw Material"
    return cat


def normalize_flow_type(flow_type: str, category: str) -> str:
    ft = flow_type.strip()
    if ft in {"Input", "Output"}:
        return ft
    if category in {
        "Raw Material",
        "Process Energy",
        "Post-processing Energy",
        "Feedstock Energy",
        "Gas",
        "Cooling Media",
    }:
        return "Input"
    if category in {"Product", "Recovered Material", "Waste", "Emission"}:
        return "Output"
    return ft or "Input"


def normalize_record(record: Dict[str, Any]) -> Dict[str, Any] | None:
    flow_name = (
        record.get("flow_name")
        or record.get("name")
        or record.get("flow")
        or ""
    )
    category = record.get("category") or ""
    unit = record.get("unit") or ""
    flow_type = record.get("flow_type") or record.get("type") or ""
    value = record.get("value")
    chunk_id = record.get("chunk_id") or ""
    note = record.get("note") or ""

    if flow_name is None:
        flow_name = ""
    flow_name = str(flow_name).strip()
    category = str(category).strip()
    unit = str(unit).strip()
    flow_type = str(flow_type).strip()
    note = str(note).strip()

    if not flow_name or value is None:
        return None

    try:
        value = float(value)
    except (TypeError, ValueError):
        return None

    value, unit = normalize_unit_and_value(value, unit)
    category = normalize_category(category, flow_name)
    flow_type = normalize_flow_type(flow_type, category)

    return {
        "flow_name": flow_name,
        "category": category,
        "value": value,
        "unit": unit,
        "flow_type": flow_type,
        "chunk_id": str(chunk_id).strip(),
        "note": note,
    }


class SafeEvaluator(ast.NodeVisitor):
    ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod)
    ALLOWED_UNARYOPS = (ast.UAdd, ast.USub)

    def __init__(self, variables: Optional[Dict[str, float]] = None):
        self.variables = variables or {}

    def visit_Expression(self, node: ast.Expression) -> float:
        return self.visit(node.body)

    def visit_BinOp(self, node: ast.BinOp) -> float:
        if not isinstance(node.op, self.ALLOWED_BINOPS):
            raise ValueError("Unsupported operator")
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Pow):
            return left ** right
        if isinstance(node.op, ast.Mod):
            return left % right
        raise ValueError("Unsupported operator")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> float:
        if not isinstance(node.op, self.ALLOWED_UNARYOPS):
            raise ValueError("Unsupported unary operator")
        value = self.visit(node.operand)
        return +value if isinstance(node.op, ast.UAdd) else -value

    def visit_Name(self, node: ast.Name) -> float:
        if node.id not in self.variables:
            raise ValueError(f"Unknown variable: {node.id}")
        return float(self.variables[node.id])

    def visit_Constant(self, node: ast.Constant) -> float:
        if not isinstance(node.value, (int, float)):
            raise ValueError("Only numeric constants are allowed")
        return float(node.value)

    def generic_visit(self, node: ast.AST) -> float:
        raise ValueError(f"Unsupported expression: {type(node).__name__}")


def safe_calculate(expression: str, variables: Optional[Dict[str, float]] = None) -> float:
    tree = ast.parse(expression, mode="eval")
    evaluator = SafeEvaluator(variables=variables)
    return evaluator.visit(tree)


def build_tools_schema() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "search_document",
                "description": "Search the uploaded document for relevant quantitative evidence.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Single search query."},
                        "queries": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Batch search queries.",
                        },
                        "max_results": {"type": "integer", "description": "Maximum results to return."},
                    },
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "define_lca_scope",
                "description": "Record the functional unit or other scope information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "parameter_name": {"type": "string"},
                        "description": {"type": "string"},
                        "value": {"type": ["number", "null"]},
                        "unit": {"type": ["string", "null"]},
                        "selected_chunk": {
                            "type": "object",
                            "properties": {
                                "chunk_id": {"type": "string"},
                                "content": {"type": "string"},
                            },
                            "required": ["chunk_id", "content"],
                            "additionalProperties": False,
                        },
                        "note": {"type": "string"},
                    },
                    "required": ["parameter_name", "description"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "record_process_flow",
                "description": "Record a quantitative LCI flow.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "flow_type": {"type": "string", "description": "Input or Output"},
                        "category": {"type": "string", "description": "LCI category"},
                        "name": {"type": "string", "description": "Flow name"},
                        "value": {"type": "number", "description": "Flow quantity"},
                        "unit": {"type": "string", "description": "Flow unit"},
                        "note": {"type": "string"},
                        "selected_chunk": {
                            "type": "object",
                            "properties": {
                                "chunk_id": {"type": "string"},
                                "content": {"type": "string"},
                            },
                            "required": ["chunk_id", "content"],
                            "additionalProperties": False,
                        },
                    },
                    "required": ["flow_type", "category", "name", "value", "unit"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "record_parameter",
                "description": "Record an intermediate parameter for later calculation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "parameter_name": {"type": "string"},
                        "value": {"type": "number"},
                        "unit": {"type": "string"},
                        "note": {"type": "string"},
                        "selected_chunk": {
                            "type": "object",
                            "properties": {
                                "chunk_id": {"type": "string"},
                                "content": {"type": "string"},
                            },
                            "required": ["chunk_id", "content"],
                            "additionalProperties": False,
                        },
                    },
                    "required": ["parameter_name", "value", "unit"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "execute_calculation",
                "description": "Execute a deterministic arithmetic calculation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"},
                        "variables": {"type": "object", "additionalProperties": {"type": "number"}},
                    },
                    "required": ["expression"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_session_summary",
                "description": "Get a summary of the already recorded scope, parameters, and flows.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
        },
    ]


def tool_search_document(state: SessionState, args: Dict[str, Any], default_top_k: int) -> Dict[str, Any]:
    max_results = int(args.get("max_results") or default_top_k)
    queries = args.get("queries")
    query = args.get("query")

    if isinstance(queries, list) and queries:
        query_list = [str(q).strip() for q in queries if str(q).strip()]
    elif isinstance(query, str) and query.strip():
        query_list = [query.strip()]
    else:
        return {"success": False, "error": "search_document requires query or queries"}

    results: List[Dict[str, Any]] = []
    seen: set[str] = set()
    per_query_limit = max(1, min(max_results, default_top_k))

    for q in query_list:
        for chunk in retrieve_top_k(q, state.chunks, top_k=per_query_limit):
            key = f"{chunk.chunk_id}::{normalize_text(chunk.content)}"
            if key in seen:
                continue
            seen.add(key)
            results.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content,
                    "score": round(lexical_score(q, chunk.content), 4),
                }
            )
            if len(results) >= max_results:
                break
        if len(results) >= max_results:
            break

    return {
        "success": True,
        "message": f"Found {len(results)} relevant results",
        "results": results,
        "queries": query_list,
    }


def tool_define_lca_scope(state: SessionState, args: Dict[str, Any]) -> Dict[str, Any]:
    action_id = state.next_action_id()
    scope = {
        "action_id": action_id,
        "session_id": state.session_id,
        "parameter_name": args.get("parameter_name"),
        "description": args.get("description"),
        "value": args.get("value"),
        "unit": args.get("unit"),
        "selected_chunk": args.get("selected_chunk"),
        "note": args.get("note"),
    }
    state.scopes.append(scope)
    return {
        "success": True,
        "message": f"Successfully defined LCA scope: {scope['parameter_name']}",
        "data": scope,
    }


def tool_record_process_flow(state: SessionState, args: Dict[str, Any]) -> Dict[str, Any]:
    record = normalize_record(
        {
            "flow_name": args.get("name"),
            "category": args.get("category"),
            "value": args.get("value"),
            "unit": args.get("unit"),
            "flow_type": args.get("flow_type"),
            "chunk_id": (args.get("selected_chunk") or {}).get("chunk_id", ""),
            "note": args.get("note", ""),
        }
    )
    if not record:
        return {"success": False, "error": "Invalid record_process_flow arguments"}

    action_id = state.next_action_id()
    stored = {
        "record_id": action_id,
        "action_id": action_id,
        "session_id": state.session_id,
        "flow_type": record["flow_type"],
        "category": record["category"],
        "name": record["flow_name"],
        "value": record["value"],
        "unit": record["unit"],
        "note": record.get("note", ""),
        "selected_chunk": args.get("selected_chunk"),
        "chunk_id": record["chunk_id"],
    }
    state.records.append(record)
    return {
        "success": True,
        "message": f"Successfully recorded process flow: {record['flow_name']}",
        "data": stored,
    }


def tool_record_parameter(state: SessionState, args: Dict[str, Any]) -> Dict[str, Any]:
    action_id = state.next_action_id()
    item = {
        "action_id": action_id,
        "session_id": state.session_id,
        "parameter_name": args.get("parameter_name"),
        "value": args.get("value"),
        "unit": args.get("unit"),
        "note": args.get("note", ""),
        "selected_chunk": args.get("selected_chunk"),
    }
    state.parameters.append(item)
    return {
        "success": True,
        "message": f"Successfully recorded parameter: {item['parameter_name']}",
        "data": {"new_action_id": action_id, **item},
    }


def tool_execute_calculation(state: SessionState, args: Dict[str, Any]) -> Dict[str, Any]:
    expression = str(args.get("expression", "")).strip()
    variables = args.get("variables") or {}
    try:
        result = safe_calculate(expression, variables)
    except Exception as exc:
        return {
            "success": False,
            "expression": expression,
            "error": f"Calculation failed: {exc}",
        }

    action_id = state.next_action_id()
    state.calculations.append(
        {
            "action_id": action_id,
            "expression": expression,
            "variables": variables,
            "result": result,
        }
    )
    return {
        "success": True,
        "expression": expression,
        "result": result,
        "data": {"new_action_id": action_id},
    }


def tool_get_session_summary(state: SessionState, _args: Dict[str, Any]) -> Dict[str, Any]:
    lines = []
    if state.scopes:
        lines.append("Scopes:")
        for scope in state.scopes:
            lines.append(f"- {scope['parameter_name']}: {scope['description']}")
    if state.parameters:
        lines.append("Parameters:")
        for param in state.parameters:
            lines.append(f"- {param['parameter_name']} = {param['value']} {param['unit']}")
    if state.records:
        lines.append("Recorded flows:")
        for record in state.records:
            lines.append(
                f"- {record['flow_type']} | {record['category']} | "
                f"{record['flow_name']} | {record['value']} {record['unit']}"
            )
    if not lines:
        lines.append("No scope, parameter, or flow has been recorded yet.")

    return {
        "success": True,
        "message": "Session summary generated",
        "data": {
            "text_summary": "\n".join(lines),
            "records": state.records,
            "parameters": state.parameters,
            "scopes": state.scopes,
        },
    }


def dispatch_tool(
    state: SessionState,
    tool_name: str,
    args: Dict[str, Any],
    top_k: int,
) -> Dict[str, Any]:
    if tool_name == "search_document":
        return tool_search_document(state, args, default_top_k=top_k)
    if tool_name == "define_lca_scope":
        return tool_define_lca_scope(state, args)
    if tool_name == "record_process_flow":
        return tool_record_process_flow(state, args)
    if tool_name == "record_parameter":
        return tool_record_parameter(state, args)
    if tool_name == "execute_calculation":
        return tool_execute_calculation(state, args)
    if tool_name == "get_session_summary":
        return tool_get_session_summary(state, args)
    return {"success": False, "error": f"Unknown tool: {tool_name}"}


def openai_chat_completion(
    api_base: str,
    api_key: str,
    model: str,
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    temperature: float,
    max_completion_tokens: int,
    timeout: int,
) -> Dict[str, Any]:
    url = f"{api_base.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
        "temperature": temperature,
        "max_completion_tokens": max_completion_tokens,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def normalize_assistant_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif "text" in item:
                    parts.append(str(item.get("text", "")))
            else:
                parts.append(str(item))
        return "\n".join(p for p in parts if p)
    return str(content)


def parse_tool_arguments(raw_args: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(raw_args or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def build_messages_for_sample(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    system_prompt = ""
    user_prompt = ""
    for msg in messages:
        if msg.get("role") == "system" and not system_prompt:
            system_prompt = msg.get("content", "")
        elif msg.get("role") == "user" and not user_prompt:
            user_prompt = msg.get("content", "")

    if not system_prompt:
        system_prompt = (
            "You are an expert LCA assistant. Use the available tools to search "
            "the document and record grounded quantitative LCI flows."
        )

    if not user_prompt:
        user_prompt = "Extract the requested LCI data from the document."

    benchmark_note = (
        "\n\n## Benchmark Note\n"
        "This evaluation harness automatically manages the session internally.\n"
        "Use the provided tools directly. Do not ask the user for session_id.\n"
        "Record only quantitative flows grounded in the document evidence.\n"
        "When recording flows, use the project LCI categories and canonical units.\n"
    )

    return [
        {"role": "system", "content": system_prompt + benchmark_note},
        {"role": "user", "content": user_prompt},
    ]


def process_file(
    filepath: Path,
    api_base: str,
    api_key: str,
    model: str,
    top_k: int,
    temperature: float,
    max_completion_tokens: int,
    max_turns: int,
    timeout: int,
    verbose: bool = False,
) -> Dict[str, Any]:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    dialogues = data if isinstance(data, list) else [data]
    if not dialogues:
        return {"file": filepath.name, "type": "SHORT_E", "tool_calls": [], "records": []}

    dialogue = dialogues[0]
    source_messages = dialogue.get("messages", [])
    initial_messages = build_messages_for_sample(source_messages)
    user_request = extract_user_request(source_messages)
    chunks = extract_chunks_from_messages(source_messages)
    state = SessionState(session_id=f"openai_{filepath.stem}", chunks=chunks)
    tools = build_tools_schema()
    messages: List[Dict[str, Any]] = list(initial_messages)
    tool_call_log: List[Dict[str, Any]] = []

    if verbose:
        print(f"\n=== {filepath.name} ===")
        print(f"User request: {user_request}")
        print(f"Evidence chunks available: {len(chunks)}")

    last_content = ""

    try:
        for turn in range(max_turns):
            response = openai_chat_completion(
                api_base=api_base,
                api_key=api_key,
                model=model,
                messages=messages,
                tools=tools,
                temperature=temperature,
                max_completion_tokens=max_completion_tokens,
                timeout=timeout,
            )
            choice = response["choices"][0]
            message = choice["message"]
            assistant_content = normalize_assistant_content(message.get("content"))
            assistant_tool_calls = message.get("tool_calls") or []
            last_content = assistant_content

            assistant_message_for_history: Dict[str, Any] = {
                "role": "assistant",
                "content": assistant_content,
            }
            if assistant_tool_calls:
                assistant_message_for_history["tool_calls"] = assistant_tool_calls
            messages.append(assistant_message_for_history)

            if not assistant_tool_calls:
                break

            for tool_call in assistant_tool_calls:
                call_id = tool_call["id"]
                function = tool_call["function"]
                tool_name = function["name"]
                args = parse_tool_arguments(function.get("arguments", "{}"))

                tool_call_log.append(
                    {
                        "id": call_id,
                        "name": tool_name,
                        "arguments": args,
                    }
                )

                result = dispatch_tool(state, tool_name, args, top_k=top_k)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

                if verbose:
                    print(f"  tool: {tool_name} -> {result.get('message', result.get('error', 'ok'))}")

        output = {
            "file": filepath.name,
            "type": "SHORT_E",
            "user_request": user_request,
            "tool_calls": tool_call_log,
            "records": state.records,
            "turns": len(messages),
        }
        if last_content:
            output["final_response"] = last_content
        return output
    except Exception as exc:
        if verbose:
            print(f"  ERROR: {exc}")
        return {
            "file": filepath.name,
            "type": "SHORT_E",
            "user_request": user_request,
            "tool_calls": tool_call_log,
            "records": state.records,
            "turns": len(messages),
            "error": str(exc),
        }


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OpenAI tool-calling baseline on SHORT_E.")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="OpenAI API base URL.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name, e.g. gpt-4.1-mini or gpt-5-mini.")
    parser.add_argument("--test-dir", default=DEFAULT_TEST_DIR, help="Directory containing SHORT_E files.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output predictions JSON path.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="Top-k evidence chunks per search call.")
    parser.add_argument("--temperature", type=float, default=0.1, help="Sampling temperature.")
    parser.add_argument("--max-completion-tokens", type=int, default=1200, help="Max completion tokens.")
    parser.add_argument("--max-turns", type=int, default=8, help="Maximum assistant turns per sample.")
    parser.add_argument("--timeout", type=int, default=120, help="HTTP timeout in seconds.")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N files.")
    parser.add_argument("--verbose", action="store_true", help="Print per-sample tool activity.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set. Please export it before running this script.")

    test_dir = Path(args.test_dir)
    if not test_dir.exists():
        raise SystemExit(f"Test directory not found: {test_dir}")

    files = sorted(test_dir.glob("*.json"))
    if args.limit is not None:
        files = files[: args.limit]
    if not files:
        raise SystemExit(f"No JSON files found in {test_dir}")

    started = time.time()
    predictions: List[Dict[str, Any]] = []

    for filepath in files:
        predictions.append(
            process_file(
                filepath=filepath,
                api_base=args.api_base,
                api_key=api_key,
                model=args.model,
                top_k=args.top_k,
                temperature=args.temperature,
                max_completion_tokens=args.max_completion_tokens,
                max_turns=args.max_turns,
                timeout=args.timeout,
                verbose=args.verbose,
            )
        )

    output_path = Path(args.output)
    save_json(output_path, predictions)

    metadata = {
        "model": args.model,
        "api_base": args.api_base,
        "test_dir": str(test_dir),
        "num_files": len(files),
        "top_k": args.top_k,
        "temperature": args.temperature,
        "max_completion_tokens": args.max_completion_tokens,
        "max_turns": args.max_turns,
        "timeout": args.timeout,
        "elapsed_seconds": round(time.time() - started, 2),
    }
    save_json(output_path.parent / "metadata.json", metadata)

    print(f"Saved predictions to: {output_path}")
    print(f"Saved metadata to: {output_path.parent / 'metadata.json'}")


if __name__ == "__main__":
    main()
