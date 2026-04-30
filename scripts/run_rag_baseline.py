#!/usr/bin/env python3
"""
RAG-only baseline for SHORT_E evaluation.

Design goal:
1. Reuse the existing SHORT_E test dialogues in test_data/short_extract.
2. Do NOT use the original tool-calling workflow.
3. Build a lightweight retrieval corpus from chunk previews and tool search results
   already embedded in the dialogue files.
4. Retrieve top-k chunks for the user request.
5. Ask the base model to directly output structured LCI records in JSON.

This is intentionally a simpler baseline than EcoLLM:
- retrieval + direct extraction
- no parameter tool
- no calculation tool
- no record tool
- no iterative tool loop

Expected output format:
[
  {
    "file": "short_001_complete.json",
    "type": "SHORT_E",
    "records": [
      {
        "flow_name": "...",
        "category": "...",
        "value": 1.23,
        "unit": "kWh",
        "flow_type": "Input"
      }
    ]
  }
]
"""

from __future__ import annotations

import argparse
import json
import re
import string
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests


DEFAULT_MODEL = "qwen-lca"
DEFAULT_VLLM_BASE = "http://localhost:8080/v1"
DEFAULT_TEST_DIR = "test_data/short_extract"
DEFAULT_OUTPUT = "results/rag_only_qwen3_8b/predictions.json"


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


def normalize_text(text: str) -> str:
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> List[str]:
    norm = normalize_text(text)
    return [tok for tok in norm.split() if tok and tok not in STOPWORDS]


def extract_json_from_tool_response(content: str) -> Dict[str, Any] | None:
    """
    Tool messages are often wrapped like:
    <tool_response>
    { ...json... }
    </tool_response>
    """
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

    # Match blocks like:
    # **CHUNK 0 PREVIEW** ... "...."
    pattern = re.compile(
        r"\*\*CHUNK\s+(\d+)\s+PREVIEW.*?\*\*:\s*\"(.*?)\"",
        re.DOTALL,
    )
    for match in pattern.finditer(system_content or ""):
        chunk_id = match.group(1)
        content = match.group(2).strip()
        if content:
            chunks.append(Chunk(chunk_id=f"preview_{chunk_id}", content=content, source="system_preview"))
    return chunks


def extract_chunks_from_messages(messages: List[Dict[str, Any]]) -> List[Chunk]:
    chunks: List[Chunk] = []

    # 1. System prompt preview chunks
    for msg in messages:
        if msg.get("role") == "system":
            chunks.extend(extract_preview_chunks(msg.get("content", "")))

    # 2. Tool search results
    for msg in messages:
        if msg.get("role") != "tool":
            continue
        payload = extract_json_from_tool_response(msg.get("content", ""))
        if not payload:
            continue
        results = payload.get("results", [])
        for item in results:
            chunk_id = str(item.get("chunk_id", "unknown"))
            content = (item.get("content") or "").strip()
            if content:
                chunks.append(Chunk(chunk_id=chunk_id, content=content, source="tool_search"))

    return deduplicate_chunks(chunks)


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


def lexical_score(query: str, chunk_text: str) -> float:
    q_tokens = tokenize(query)
    c_tokens = tokenize(chunk_text)
    if not q_tokens or not c_tokens:
        return 0.0

    q_set = set(q_tokens)
    c_set = set(c_tokens)
    overlap = q_set & c_set

    # Weighted overlap ratio
    overlap_score = len(overlap) / max(len(q_set), 1)

    # Numeric hint: prefer chunks that contain explicit numbers
    has_number = 1.0 if re.search(r"\d", chunk_text) else 0.0

    # Table hint: many useful records come from tables
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


def build_prompt(user_request: str, chunks: List[Chunk]) -> List[Dict[str, str]]:
    system_prompt = """You are an LCA extraction assistant.

Your task is to extract explicit LCI records from retrieved document passages.

Return valid JSON only with the following structure:
{
  "records": [
    {
      "flow_name": "string",
      "category": "one allowed category",
      "value": number,
      "unit": "canonical unit",
      "flow_type": "Input or Output",
      "chunk_id": "supporting chunk id"
    }
  ]
}

Rules:
1. Only extract records explicitly supported by the retrieved passages.
2. Do not invent missing values.
3. Do not perform hidden multi-step planning; just extract from the provided evidence.
4. If no valid record is found, return {"records": []}.
5. Use ONLY these categories:
   - Raw Material
   - Process Energy
   - Post-processing Energy
   - Feedstock Energy
   - Gas
   - Cooling Media
   - Product
   - Recovered Material
   - Waste
   - Emission
6. Do NOT use vague categories such as "Energy" or "Material".
7. Prefer these canonical units:
   - mass: kg
   - electricity: kWh
   - gas volume: m³
   - liquid cooling media: L
8. Use "Input" for raw materials, energy, gas, and cooling media.
9. Use "Output" for product, recovered material, waste, and emissions.
10. If the evidence says grams, convert to kg.
11. Each record must include the chunk_id of the supporting evidence.
12. Output JSON only. No explanation, no markdown fence, no extra text.
"""

    evidence_blocks = []
    for idx, chunk in enumerate(chunks, 1):
        evidence_blocks.append(
            f"[Evidence {idx} | chunk_id={chunk.chunk_id} | source={chunk.source}]\n{chunk.content}"
        )

    user_prompt = (
        f"User request:\n{user_request}\n\n"
        f"Retrieved passages:\n\n{chr(10).join(evidence_blocks)}\n\n"
        "Return only the JSON object."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def parse_model_json(content: str) -> Dict[str, Any]:
    raw = content.strip()

    # Remove code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    # Try full parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Fallback: incrementally decode first valid JSON object
    decoder = json.JSONDecoder()
    for start in range(len(raw)):
        if raw[start] != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(raw[start:])
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue

    raise ValueError("Model response does not contain valid JSON.")


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
        # If the model says coarse "energy", use name hint
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
    chunk_id = record.get("chunk_id") or record.get("source_chunk_id") or ""

    if flow_name is None:
        flow_name = ""
    flow_name = str(flow_name).strip()
    category = str(category).strip()
    unit = str(unit).strip()
    flow_type = str(flow_type).strip()

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
    }


def call_vllm_chat(
    api_base: str,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
    timeout: int,
) -> str:
    url = f"{api_base.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def process_file(
    filepath: Path,
    api_base: str,
    model: str,
    top_k: int,
    temperature: float,
    max_tokens: int,
    timeout: int,
    verbose: bool = False,
) -> Dict[str, Any]:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    dialogues = data if isinstance(data, list) else [data]
    if not dialogues:
        return {"file": filepath.name, "type": "SHORT_E", "records": []}

    dialogue = dialogues[0]
    messages = dialogue.get("messages", [])
    user_request = extract_user_request(messages)
    all_chunks = extract_chunks_from_messages(messages)
    retrieved = retrieve_top_k(user_request, all_chunks, top_k=top_k)
    prompt_messages = build_prompt(user_request, retrieved)

    if verbose:
        print(f"\n=== {filepath.name} ===")
        print(f"User request: {user_request}")
        print(f"Available chunks: {len(all_chunks)} | Retrieved: {len(retrieved)}")
        for idx, chunk in enumerate(retrieved, 1):
            preview = chunk.content[:120].replace("\n", " ")
            print(f"  {idx}. {chunk.chunk_id} [{chunk.source}] {preview}...")

    try:
        content = call_vllm_chat(
            api_base=api_base,
            model=model,
            messages=prompt_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        payload = parse_model_json(content)
        records = payload.get("records", [])
        normalized = []
        for record in records:
            if isinstance(record, dict):
                norm = normalize_record(record)
                if norm:
                    normalized.append(norm)
        return {
            "file": filepath.name,
            "type": "SHORT_E",
            "records": normalized,
        }
    except Exception as exc:
        if verbose:
            print(f"  ERROR: {exc}")
        return {
            "file": filepath.name,
            "type": "SHORT_E",
            "records": [],
            "error": str(exc),
        }


def check_vllm_health(api_base: str, timeout: int) -> None:
    url = f"{api_base.rstrip('/')}/models"
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RAG-only baseline on SHORT_E test set.")
    parser.add_argument("--test-dir", default=DEFAULT_TEST_DIR, help="Directory with SHORT_E complete json files.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output predictions json path.")
    parser.add_argument("--api-base", default=DEFAULT_VLLM_BASE, help="vLLM OpenAI-compatible API base.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Served model name in vLLM.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of retrieved chunks.")
    parser.add_argument("--temperature", type=float, default=0.15, help="Sampling temperature.")
    parser.add_argument("--max-tokens", type=int, default=1200, help="Max generation tokens.")
    parser.add_argument("--timeout", type=int, default=120, help="HTTP timeout in seconds.")
    parser.add_argument("--limit", type=int, default=0, help="Optional limit on number of files.")
    parser.add_argument("--verbose", action="store_true", help="Print per-sample details.")
    args = parser.parse_args()

    test_dir = Path(args.test_dir)
    if not test_dir.exists():
        raise SystemExit(f"Test directory does not exist: {test_dir}")

    files = sorted(test_dir.glob("*_complete.json"))
    if args.limit > 0:
        files = files[: args.limit]
    if not files:
        raise SystemExit(f"No test files found in: {test_dir}")

    print("Checking vLLM service...")
    check_vllm_health(args.api_base, args.timeout)
    print(f"vLLM is reachable at {args.api_base}")
    print(f"Model: {args.model}")
    print(f"Samples to run: {len(files)}")

    predictions: List[Dict[str, Any]] = []
    num_failed = 0

    for idx, filepath in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] {filepath.name}")
        pred = process_file(
            filepath=filepath,
            api_base=args.api_base,
            model=args.model,
            top_k=args.top_k,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
            verbose=args.verbose,
        )
        if not pred.get("records"):
            num_failed += 1
        predictions.append(pred)

    output_path = Path(args.output)
    save_json(output_path, predictions)

    metadata = {
        "baseline": "rag_only",
        "model": args.model,
        "api_base": args.api_base,
        "test_dir": str(test_dir),
        "num_samples": len(files),
        "top_k": args.top_k,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "failed_samples": num_failed,
    }
    save_json(output_path.parent / "metadata.json", metadata)

    total_preds = sum(len(item.get("records", [])) for item in predictions)
    print("\nDone.")
    print(f"Predictions saved to: {output_path}")
    print(f"Metadata saved to: {output_path.parent / 'metadata.json'}")
    print(f"Total predicted records: {total_preds}")
    print(f"Failed / empty samples: {num_failed}/{len(files)}")


if __name__ == "__main__":
    main()
