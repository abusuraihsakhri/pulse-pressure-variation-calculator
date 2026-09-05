# Pulse Pressure Variation Calculator

> **Domain:** Clinical Decision Support & Biomedical Computing

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## What It Does

Pulse Pressure Variation Calculator computes clinical scores from laboratory values and physiological measurements. Supports MELD-Na, QTc (Bazett), BMI z-score, HbA1c/eAG conversion, APRI/FIB-4, and generic scoring.

---

## Key Modules

### Core Calculators (`ppv.py`)
- **`assess_row()`** — Routes input rows to the appropriate calculator based on detected keys.
- **`calculate_meld_na()`** — MELD-Na score for liver disease severity.
- **`calculate_qtc()`** — Corrected QT interval using Bazett's formula.
- **`calculate_bmi_z()`** — BMI computation for pediatric patients.
- **`convert_hba1c()`** — Converts between HbA1c (%) and estimated average glucose (mg/dL).
- **`calculate_apri_fib4()`** — APRI and FIB-4 scores for liver fibrosis assessment.
- **`process_csv()`** — Batch processes CSV files through the calculator pipeline.

### Enterprise Agent Framework (`agents/`)
- **SystemSupervisor** — Multi-worker orchestration with PHI guard and HMAC-SHA256 audit trail.
- **Specialized Workers** — InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker.
- **FastAPI Server** — REST endpoints at `/api/audit`, `/api/chat`, `/api/audit/logs`, `/health`, `/metrics`.

---

## Quickstart

### Installation
```bash
pip install -e ".[dev]"
```

### CLI Usage
```bash
# Single calculation
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch CSV processing
python cli.py batch -i sample.csv -o results.csv

# Verify audit trail
python cli.py verify-audit

# Launch API server
python cli.py serve --host 127.0.0.1 --port 8000
```

### Direct Python Usage
```python
from ppv import assess_row

# MELD-Na calculation
result = assess_row({"bilirubin": 2.5, "creatinine": 1.2, "inr": 1.1, "sodium": 138})

# QTc calculation
result = assess_row({"qt_ms": 420, "hr_bpm": 72})

# Generic scoring
result = assess_row({"value": 10, "qty": 2})
```

---

## Input Data Schema

| Field | Description | Used By |
|:------|:------------|:--------|
| `bilirubin` | Bilirubin level (mg/dL) | MELD-Na |
| `creatinine` | Creatinine level (mg/dL) | MELD-Na |
| `inr` | International Normalized Ratio | MELD-Na |
| `sodium` | Sodium level (mEq/L) | MELD-Na |
| `qt_ms` / `qt` | QT interval (ms) | QTc |
| `hr_bpm` / `heart_rate` | Heart rate (bpm) | QTc |
| `weight_kg` | Weight in kilograms | BMI |
| `height_cm` | Height in centimeters | BMI |
| `hba1c_percent` | HbA1c percentage | HbA1c conversion |
| `eag_mgdl` | Estimated average glucose | HbA1c conversion |
| `ast_u_l` | AST level (U/L) | APRI/FIB-4 |

---

## Security

- **Zero-PHI Outbound Interceptor:** AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
- **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation.
- **Environment-based Secret Management:** `AUDIT_SECRET_KEY` must be set in production (no hardcoded defaults).

---

## Testing

```bash
# Run full test suite
pytest -v

# Run with coverage
pytest -v --cov=.

# Run simulation benchmark
python simulator.py 1000
```

---

## Container Deployment

```bash
# Build and run with Docker Compose
AUDIT_SECRET_KEY=your-secret-key docker-compose up --build

# Or with Docker directly
docker build -t pulse-pressure-variation-calculator .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key pulse-pressure-variation-calculator
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
