# Fixture Guide

This guide provides an overview of the new fixture example system and how to use it effectively.

## Overview
The `backend/tests/examples` directory contains practical, runnable examples demonstrating fixture usage at different levels of complexity.

## Example Directories
- **basic/**: Simple patterns for beginners (authentication, database, API)
- **api/**: Endpoint testing examples, including error cases and mocking
- **integration/**: Advanced end-to-end and performance testing workflows
- **templates/**: Reusable template scripts for quick test scaffolding

## Getting Started
1. Choose the appropriate example directory based on your skill level and testing scenario.
2. Copy the example script to your test suite and adapt it as needed.
3. Run the example test to verify fixture integration.

## Navigation
Each subdirectory contains a `README.md` with detailed instructions and code comments.

## Contributing New Examples
To add a new example:
1. Create a script under the relevant directory.
2. Update the directory's `README.md` with a description of the new example.
3. Ensure the example uses the fixtures defined in `backend/tests/fixtures`.
4. Add tests for the example if necessary. 