"""ID generation utilities for different content types."""

from pathlib import Path


def generate_doc_id(file_path: str) -> str:
    """Generate a unique ID for documentation files."""
    # Remove 'docs/' prefix and file extension, replace separators with dots
    doc_path = file_path.replace("docs/", "").replace("/", ".").replace("\\", ".")
    if doc_path.endswith(".md"):
        doc_path = doc_path[:-3]
    elif doc_path.endswith(".txt"):
        doc_path = doc_path[:-4]
    elif doc_path.endswith(".json"):
        doc_path = doc_path[:-5]
    return f"doc.{doc_path}"


def generate_design_id(file_path: str) -> str:
    """Generate a unique ID for design files."""
    # Remove 'design/' prefix and file extension, replace separators with dots
    design_path = (
        file_path.replace("design/", "").replace("/", ".").replace("\\", ".")
    )
    if design_path.endswith(".json"):
        design_path = design_path[:-5]
    return f"design.{design_path}"


def generate_readme_id(file_path: str) -> str:
    """Generate a unique ID for README files based on their directory path."""
    path_obj = Path(file_path)

    # If it's in the root, just use "readme"
    if str(path_obj.parent) == "." or path_obj.parent.name == "":
        return "doc-readme"

    # Generate ID based on directory path
    # /project/docs/README.md -> doc-readme.docs
    # /project/backend/README.md -> doc-readme.backend
    # /project/docs/api/README.md -> doc-readme.docs.api
    parent_path = str(path_obj.parent).replace("/", ".").replace("\\", ".")

    # Remove common prefixes to keep IDs clean (only if it's exactly "./" prefix)
    if parent_path.startswith("./") and len(parent_path) > 2 and parent_path[2] != ".":
        parent_path = parent_path[2:]

    return f"doc-readme.{parent_path}"


def generate_path_based_id(file_path: str, base_name: str) -> str:
    """Generate a unique ID for common duplicate filenames using directory path."""
    path_obj = Path(file_path)

    # If it's in the root, just use the base name
    if str(path_obj.parent) == "." or path_obj.parent.name == "":
        return f"doc-{base_name}"

    # Generate ID based on directory path
    # /project/frontend/src/index.ts -> doc-index.frontend.src
    # /project/backend/config.py -> doc-config.backend
    parent_path = str(path_obj.parent).replace("/", ".").replace("\\", ".")

    # Remove common prefixes to keep IDs clean (only if it's exactly "./" prefix)
    if parent_path.startswith("./") and len(parent_path) > 2 and parent_path[2] != ".":
        parent_path = parent_path[2:]

    return f"doc-{base_name}.{parent_path}"


def generate_code_id(file_path: str) -> str:
    """Generate a unique ID for code files."""
    # Normalize path and remove file extension
    code_path = file_path.replace("/", ".").replace("\\", ".")
    if code_path.endswith((".py", ".ts", ".tsx", ".js", ".jsx")):
        code_path = code_path.rsplit(".", 1)[0]
    return f"code.{code_path}"