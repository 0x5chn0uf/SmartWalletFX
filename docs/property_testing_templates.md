# Property-Based Testing Templates

This guide explains how the reusable property-based testing templates work and how you can
extend them when adding new features.

---

## Why Property-Based Testing?

Traditional example-based tests cover only the cases we think of. By contrast,
property-based testing generates _many_ random inputs and asserts that high-level
invariants always hold. This approach excels at finding edge-cases and keeps
our test-suite resilient as the input space evolves.

We rely on **Hypothesis** to generate data and **Pytest** to run the templates.

---

## Directory Layout

```text
backend/tests/
├── strategies/          # Shared Hypothesis strategies
│   └── security.py      # strong_passwords(), email_addresses(), …
├── templates/           # Template libraries collected once per test run
│   ├── auth_property_tests.py        # Authentication invariants
│   ├── constant_time_tests.py        # Timing-attack assertions
│   └── test_auth_property_templates.py   # Strategy ↔ validator coherence
└── plugins/
    └── property_templates.py         # Pytest plugin – auto marker & Hypothesis profile
```

### Key Points

1. _Templates_ are collected exactly once and should **not** depend on specific
   business logic – they validate _global_ invariants.
2. Each template module carries or receives the `pytest.mark.property` marker so
   it can be filtered via `pytest -m property`.
3. The plugin auto-adds the marker to any file under `tests/templates/`.

---

## Running Locally

```bash
# Run only the property-based templates
pytest -m property

# Or run a single template file
pytest backend/tests/templates/auth_property_tests.py
```

The default Hypothesis _fast_ profile limits example counts for quick feedback.
On CI the plugin activates the _ci_ profile (more examples, deterministic seed).

---

## Extending Templates

1. **Create a strategy** in `backend/tests/strategies/` if one does not exist.
2. **Add a template** under `backend/tests/templates/` following existing
   examples. Keep business-logic imports minimal; rely on strategies & public
   validators instead.
3. **Document invariants** in the docstring. Aim for clear, high-level
   assertions (e.g. _hash → verify round-trip_, _accepts only RFC-valid emails_).
4. **Mark slow tests** with `@settings(deadline=None)` or lower `max_examples`.

---

## CI Integration

The _property-tests_ job executes:

```bash
pytest -m property --hypothesis-show-statistics
```

A failure indicates either:

- the invariant is genuinely violated (bug 🐞), or
- the template needs to be refined (e.g. overly-strict assertion).

Follow the Hypothesis shrink-traceback to find the minimal failing case.

---

## Common Pitfalls & Tips

| Issue                                         | Tip                                                                |
| --------------------------------------------- | ------------------------------------------------------------------ |
| **Flaky tests** due to random seed            | Use deterministic profiles or set `HYPOTHESIS_PROFILE=ci`.         |
| **Long runtime** for cryptographic functions  | Disable `deadline` and keep `max_examples` modest (≤ 200).         |
| Templates failing on unrelated modules        | Ensure they only import _public_ validators, not internal helpers. |
| Duplicate effort with Security Test Framework | Re-use helpers from `tests.utils.security_testing`.                |

---

Happy fuzzing! More examples can be found in the existing template modules –
don't hesitate to add new invariants as the codebase grows.
