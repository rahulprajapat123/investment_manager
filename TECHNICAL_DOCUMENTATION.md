1) System Architecture (end-to-end)

React (Vite) frontend on :3001 calls a Flask REST API on :5000

Flask triggers a 5-stage data pipeline and writes outputs to the file system

Output artifacts: per-client formatted Excel reports

Key folders

Uploads: data/{client_id}/Uploaded_Files/

Reports: reports/{client_id}_portfolio_report.xlsx (fallback supported: {client_id}_portfolio.xlsx)

Core pipeline modules: src/ (ingestion → normalization → validation → aggregation → reporting)

2) Tech Stack (what + how it’s used)
Backend (Python)

Python 3.11: pipeline execution + server runtime (Windows-stable)

Flask 2.3+: REST API endpoints to upload files, trigger processing, serve reports

Flask-CORS 4.0+: enables cross-origin calls from React (:3001 → :5000)

Pandas 2.0+: dataframe transforms, cleaning, grouping, aggregations

OpenPyXL 3.1+: Excel read/write support for .xlsx

XlsxWriter 3.1+: multi-sheet Excel report generation + formatting + charts

Pandera 0.17+: schema-based dataframe validation + constraint checks

decimal (built-in): financial-grade precision (no float rounding errors)

Frontend (React)

React 18.2+: UI pages (Dashboard / Upload / Reports)

Vite 5.0+: dev server + build

Ant Design 5.12+: tables, upload UI, buttons, notifications

Axios 1.6+: REST calls + status polling

React Router 6.20+: routing between pages

Day.js 1.11+: date formatting in UI

3) Stage 1 — Ingestion (src/ingestion.py)

Purpose: reliably extract broker exports from inconsistent Excel formats.

Implemented capabilities

File type detection from filename patterns: trade_book, capital_gains, holdings

Tab-separated Excel fix: detects \t inside a single column export and splits into proper columns

Client + broker extraction from directory structure: .../C001/BrokerName/file.xlsx

Robust error handling: invalid files skipped with logs; missing columns flagged

Supported brokers (extensible): Schwab, Fidelity, Groww, HDFC, ICICI Direct, Zerodha

4) Stage 2 — Normalization (src/normalizer.py)

Purpose: map broker-specific columns into canonical schemas.

Canonical schemas

Trades: date, symbol, action(Buy/Sell), qty(Decimal), price(Decimal), amount(Decimal), broker_name, client_id

Capital Gains: symbol, buy_date, sell_date, quantity(Decimal), buy_price, sell_price, gain_loss, gain_type(Short/Long), client_id, broker_name

Core mechanics

broker detection → mapping dict application → date parsing (multi-format) → Decimal conversion (prec=28) → schema sanity checks

5) Stage 3 — Validation (src/validator.py + Pandera)

Purpose: enforce data quality before analytics/reporting.

Rules implemented

required fields non-null (dates, symbols)

numeric constraints: qty > 0, price > 0

categorical constraints: action ∈ {Buy,Sell}, gain_type ∈ {Short Term, Long Term}

relational constraints: sell_date >= buy_date

Handling

critical errors stop or fail the job (core malformed data)

warnings logged and included later in the report

6) Stage 4 — Aggregation & Analytics (src/aggregator.py)

Purpose: compute portfolio metrics per client (and breakdowns).

Metrics

holdings (Buy − Sell by symbol + broker)

realized gains (Short vs Long term)

transaction stats (counts, buy/sell volume)

broker distribution (assets/trades per broker)

symbol-level insights (top holdings, most traded, P&L)

Implementation style

Pandas groupby aggregations + Decimal-safe arithmetic utilities

7) Stage 5 — Report Generation (src/report_generator.py + XlsxWriter)

Purpose: produce a multi-sheet, formatted Excel report per client.

Sheets

Summary

Current Holdings

Capital Gains (ST / LT)

Transaction History

Broker Summary

Data Quality Issues

Formatting

conditional formatting (gain/loss)

currency/%/date formats

freeze panes, auto sizing

charts (portfolio distribution)

8) Flask API + React UI (Operational workflow)
Flask (flask_backend.py)

POST /api/upload stores files in data/{client_id}/Uploaded_Files/ (secure filenames, client ID auto-format: 5 → C005)

POST /api/process/{client_id} runs full pipeline and generates report (sync job + UUID tracking)

GET /api/jobs/{job_id} returns status for frontend polling

GET /api/reports/{client_id} serves report (supports both filename conventions)

React Pages

Dashboard: list clients, trigger processing, poll job status every ~2s, download when done

Upload: drag/drop multi-file upload, .xls/.xlsx validation, progress + notifications

Reports: searchable list, filters/sort, metadata display, one-click download

9) Windows Reliability Fixes (production blockers)

Async stack instability on Windows → migrated to Flask (sync WSGI)

Windows Firewall blocking Python inbound connections → added inbound rule for Python 3.11 executable

Cross-port access blocked → enabled CORS