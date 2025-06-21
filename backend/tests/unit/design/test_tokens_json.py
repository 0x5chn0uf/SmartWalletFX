import json
import re
from pathlib import Path


def test_tokens_json_valid():
    tokens_path = Path(__file__).resolve().parents[4] / "design" / "design-tokens.json"
    assert tokens_path.exists(), f"{tokens_path} missing"
    with tokens_path.open() as fp:
        data = json.load(fp)
    assert isinstance(data, dict)


def _flatten_keys(d, prefix=""):
    keys = []
    for k, v in d.items():
        path = f"{prefix}.{k}" if prefix else k
        keys.append(path)
        if isinstance(v, dict):
            keys.extend(_flatten_keys(v, path))
    return keys


def test_token_keys_pattern():
    tokens_path = Path(__file__).resolve().parents[4] / "design" / "design-tokens.json"
    data = json.loads(tokens_path.read_text())
    all_keys = _flatten_keys(data)
    pattern = re.compile(r"^[a-z0-9.]+$")
    invalid = [k for k in all_keys if not pattern.match(k)]
    assert not invalid, f"Invalid token keys found: {invalid}"
