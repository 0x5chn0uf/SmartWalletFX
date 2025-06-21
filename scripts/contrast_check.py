import json
import sys
from pathlib import Path

"""Simple WCAG AA contrast checker stub.

This script loads design/design-tokens.json, extracts `color.text.primary` and
`color.background.default` tokens and prints a placeholder contrast ratio.

Actual calculation will be implemented in subtask 70.5 using a proper contrast
library. For now the script exits with code 0 but warns if tokens missing.
"""


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    tokens_file = root / "design" / "design-tokens.json"
    if not tokens_file.exists():
        print("design-tokens.json not found", file=sys.stderr)
        sys.exit(1)
    data = json.loads(tokens_file.read_text())
    try:
        text_color = data["color"]["text"]["primary"]
        bg_color = data["color"]["background"]["default"]
    except KeyError as exc:
        print(f"Missing token: {exc}", file=sys.stderr)
        sys.exit(1)
    # Placeholder
    print(f"Contrast check stub: text {text_color} on bg {bg_color}")


if __name__ == "__main__":
    main()
