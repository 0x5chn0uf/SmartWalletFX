# Fixture Monitoring

The fixture management tool writes a metrics file `.fixture_lint_metrics.json` whenever the analysis or fix command runs. The file contains high level statistics:

- `total_fixtures` – number of fixture definitions discovered
- `duplicate_fixtures` – total fixtures that share bodies with others
- `duplicate_groups` – number of duplicate groups detected

These metrics can be tracked by CI to monitor progress as duplicates are removed over time.
