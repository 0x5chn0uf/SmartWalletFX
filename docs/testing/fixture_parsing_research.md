# Fixture Parsing Library Research

The fixture management tool requires a parsing library capable of analysing and rewriting Python code
without losing formatting. The table below summarises the main options considered.

| Library   | Accuracy & Round-trip | Speed | API Ergonomics | Notes |
|-----------|----------------------|-------|---------------|-------|
| **libcst** | Preserves formatting and comments with concrete syntax tree. Perfect round‑trip guarantees. | Moderate; written in pure Python but optimised. | Modern, typed API. Metadata system for positions. | Widely used in code mod tools. Our preferred choice. |
| **ast** | Uses Python's built‑in abstract syntax tree. Drops formatting and comments. | Fast. | Simple API, part of stdlib. | Not suitable for safe rewriting. |
| **redbaron** | Built on top of `baron` for full round‑trip. | Slower due to dynamic nodes and heavy parsing. | Node API similar to BeautifulSoup. | Project is less actively maintained. |

`libcst` offers the best balance between accuracy and maintainability. It ensures we can parse, analyse and later rewrite fixture files without losing code style or comments. Therefore the prototype will be built using `libcst`.
