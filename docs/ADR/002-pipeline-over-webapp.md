# ADR-002: Batch Pipeline over Interactive Web Application

## Status
Accepted

## Date
2026-02-23

## Context
The current architecture is a client-side SPA where users manually upload files through a browser. The real use case is: ERP exports XML files on a schedule → financial analysis should happen automatically → reports land in a folder or inbox. The browser-based approach requires human interaction for every analysis cycle, turning a 5-minute technical operation into a 5-10 day manual process.

## Decision
Build a batch processing pipeline that runs headless (no browser, no UI).

**Execution modes:**
1. CLI: `cashflow run --input /path/to/xml --config austa`
2. File watcher: auto-triggers when new XML appears in monitored folder
3. Cron: scheduled daily/weekly/monthly via crontab or systemd timer

**Not included:** Real-time dashboard, interactive drill-down, ad-hoc chart customization

## Consequences

### Positive
- Zero human interaction for routine analysis
- Can run on a server, VM, Docker container, or locally
- 5-minute SLA vs 5-10 day manual process
- Testable end-to-end with fixture data
- No session management, no UI state, no browser quirks
- Reports are reproducible and deterministic
- Fits enterprise automation workflows (Airflow, Dagster, etc.)

### Negative
- No interactive exploration (drill-down, filtering, hover tooltips)
- Users must use generated reports rather than a live dashboard
- Less "impressive" demo than a web UI
- Harder to support ad-hoc "what-if" analysis for executives

### Risks
- Users may want interactive features later → mitigated by JSON output that can feed a future thin web dashboard without redesigning the pipeline
- "Output-only" feeling may not resonate → mitigated by strong emphasis on time savings: 5-10 days→5 minutes means 20+ hours→1 hour per analysis

## Related Decisions
- ADR-006: Output-First Design (XLSX, HTML, PDF, JSON as primary deliverables)
