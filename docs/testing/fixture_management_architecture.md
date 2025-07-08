# Fixture Management Tool Architecture

This document outlines the proposed architecture for the automated fixture management system. It will evolve as the implementation progresses.

## Modules

- **parser** – static analysis of test files to extract fixtures and their dependencies.
- **deduplicator** – detect duplicate fixtures across the repository.
- **report** – generate JSON/YAML output and future HTML dashboards.
- **cli** – command line interface built with Typer.

## Data Flow

1. CLI receives a directory or file list.
2. Parser walks each file, collecting `FixtureDefinition` objects.
3. Deduplicator analyses definitions to find similar bodies and names.
4. Report generator serialises the results for CI or developer review.

## Extension Points

- **Refactoring Engine** – automatic rewriting of fixtures.
- **Visualisation** – dependency graphs rendered with graphviz or Mermaid.
- **Pre‑commit Hook** – integration to enforce standards.

This initial version focuses on the static analysis engine (parser and deduplicator) and a minimal JSON report.
