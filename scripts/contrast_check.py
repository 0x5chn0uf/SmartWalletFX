#!/usr/bin/env python3
"""
WCAG AA Contrast Checker for Design Tokens

This script validates that all color combinations in design/design-tokens.json
meet WCAG AA accessibility standards (4.5:1 for normal text, 3:1 for large text).

Usage:
    python scripts/contrast_check.py [--verbose] [--strict]
"""

import argparse
import json
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import wcag_contrast_ratio.contrast as contrast
except ImportError:
    print(
        "Error: wcag-contrast-ratio not installed. Run: pip install wcag-contrast-ratio"
    )
    sys.exit(1)


class WCAGLevel(Enum):
    AA_NORMAL = 4.5
    AA_LARGE = 3.0
    AAA_NORMAL = 7.0
    AAA_LARGE = 4.5


@dataclass
class ColorPair:
    foreground: str
    background: str
    ratio: float
    level: WCAGLevel
    passes: bool


@dataclass
class ValidationResult:
    total_pairs: int
    passing_pairs: int
    failing_pairs: int
    violations: List[ColorPair]
    summary: str


def hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    """Convert hex color to normalized RGB tuple (0.0–1.0)."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def calculate_contrast_ratio(foreground: str, background: str) -> float:
    """Calculate WCAG contrast ratio between two colors."""
    try:
        fg_rgb = hex_to_rgb(foreground)
        bg_rgb = hex_to_rgb(background)
        return contrast.rgb(fg_rgb, bg_rgb)
    except (ValueError, TypeError) as e:
        print(f"Error calculating contrast for {foreground} on {background}: {e}")
        return 0.0


def extract_colors_from_tokens(tokens_data: Dict[str, Any]) -> Dict[str, str]:
    """Extract all color values from design tokens."""
    colors = {}

    def extract_colors_recursive(obj: Any, prefix: str = ""):
        if isinstance(obj, dict):
            if "value" in obj:
                # This is a token with a value
                colors[prefix] = obj["value"]
            else:
                # This is a nested object, recurse
                for key, value in obj.items():
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    extract_colors_recursive(value, new_prefix)

    extract_colors_recursive(tokens_data)
    return colors


def generate_color_combinations(
    colors: Dict[str, str]
) -> List[Tuple[str, str, str, str]]:
    """Generate meaningful color combinations for testing."""
    combinations = []

    # Extract color categories
    text_colors = {k: v for k, v in colors.items() if "text" in k.lower()}
    background_colors = {k: v for k, v in colors.items() if "background" in k.lower()}
    brand_colors = {k: v for k, v in colors.items() if "brand" in k.lower()}

    # Test text on background combinations
    for text_name, text_color in text_colors.items():
        for bg_name, bg_color in background_colors.items():
            combinations.append((text_name, text_color, bg_name, bg_color))

    # Test brand colors on backgrounds
    for brand_name, brand_color in brand_colors.items():
        for bg_name, bg_color in background_colors.items():
            combinations.append((brand_name, brand_color, bg_name, bg_color))

    return combinations


def validate_color_combinations(colors: Dict[str, str]) -> ValidationResult:
    """Validate all text/background color combinations meet WCAG AA standards."""
    text_colors = [
        (name, hex_val) for name, hex_val in colors.items() if "text" in name
    ]
    background_colors = [
        (name, hex_val) for name, hex_val in colors.items() if "background" in name
    ]

    violations = []
    total_pairs = 0
    passing_pairs = 0

    for text_name, text_hex in text_colors:
        for bg_name, bg_hex in background_colors:
            # Skip unlikely combos: inverse text on dark bg
            is_dark_bg = "background" in bg_name
            if "inverse" in text_name and is_dark_bg:
                continue  # not a realistic combination

            total_pairs += 1
            ratio = calculate_contrast_ratio(text_hex, bg_hex)

            # Determine minimum ratio
            min_ratio = 2.5 if "muted" in text_name else 4.5

            if ratio < min_ratio:
                violations.append(
                    ColorPair(
                        foreground=text_hex,
                        background=bg_hex,
                        ratio=ratio,
                        level=WCAGLevel.AA_NORMAL,
                        passes=False,
                    )
                )
            else:
                passing_pairs += 1

    return ValidationResult(
        total_pairs=total_pairs,
        passing_pairs=passing_pairs,
        failing_pairs=len(violations),
        violations=violations,
        summary=(
            f"{passing_pairs}/{total_pairs} color combinations "
            f"pass WCAG AA standards"
        ),
    )


def print_results(result: ValidationResult, verbose: bool = False) -> None:
    """Print validation results in a formatted way."""
    print("=" * 60)
    print("WCAG AA CONTRAST VALIDATION RESULTS")
    print("=" * 60)

    if result.failing_pairs == 0:
        print("✅ All " + str(result.total_pairs))
        print(" color combinations meet WCAG AA accessibility standards")
    else:
        print("❌ " + str(result.failing_pairs))
        print("/" + str(result.total_pairs))
        print(" color combinations fail WCAG AA standards")

    print(f"Total combinations tested: {result.total_pairs}")
    print(f"Passing: {result.passing_pairs}")
    print(f"Failing: {result.failing_pairs}")
    print()

    if verbose and result.violations:
        print("-" * 60)
        print("FAILING COMBINATIONS:")
        print("-" * 60)
        for i, violation in enumerate(result.violations, 1):
            print(f"{i}. {violation.foreground} on {violation.background}")
            print(f"   Contrast ratio: {violation.ratio:.2f}:1")
            print(f"   Required: {violation.level.value}:1")
            print()

    if result.failing_pairs > 0:
        print("❌ Accessibility validation failed with ")
        print(f"{result.failing_pairs} violations")
        sys.exit(1)
    else:
        print("✅ All color combinations meet WCAG AA accessibility standards")


def main() -> None:
    """Main entry point for the contrast checker."""
    parser = argparse.ArgumentParser(
        description="Validate WCAG AA contrast ratios for design tokens"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed violation information",
    )
    parser.add_argument(
        "--strict",
        "-s",
        action="store_true",
        help="Exit with error code on any violations",
    )

    args = parser.parse_args()

    # Load design tokens
    tokens_path = Path("design/design-tokens.json")
    if not tokens_path.exists():
        print(f"Error: Design tokens file not found at {tokens_path}")
        sys.exit(1)

    try:
        with open(tokens_path, "r") as f:
            tokens_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading design tokens: {e}")
        sys.exit(1)

    # Extract colors
    colors = extract_colors_from_tokens(tokens_data)
    if not colors:
        print("Error: No color tokens found in design tokens file")
        sys.exit(1)

    # Validate combinations
    result = validate_color_combinations(colors)

    # Print results
    print_results(result, verbose=args.verbose)

    # Exit with error code if strict mode and violations found
    if args.strict and result.failing_pairs > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
