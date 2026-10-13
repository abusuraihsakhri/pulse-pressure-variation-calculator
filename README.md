# Pulse Pressure Variation Calculator

A browser-based and Python calculator for respiratory **pulse pressure variation (PPV)**, using maximum and minimum arterial pulse pressure values measured over the same respiratory cycle. The browser version requires no login, installation, backend, or external assets. The [repository-configured GitHub Pages address](https://abusuraihsakhri.github.io/pulse-pressure-variation-calculator/) has not yet been verified as live. The application also works as a local static HTML file.

## Use the calculator

1. Select **Pulse pressures** and enter PPmax and PPmin, in mmHg, or select **Systolic and diastolic pairs** to enter the blood pressures for the beats with maximal and minimal pulse pressure.
2. Select **Calculate PPV** to display the percentage and underlying pressures.
3. Optionally export the result as CSV, or select **Fill example** to evaluate PPmax = 42 and PPmin = 38 mmHg (PPV = 10%).

**Formula:** PPV (%) = 100 × (PPmax − PPmin) / ((PPmax + PPmin) / 2), where each PP = SBP − DBP from a *single beat*. Independent maxima and minima of SBP and DBP must not be combined as if they were paired beats.

Inputs must be positive, finite pulse pressures with PPmax ≥ PPmin. In paired-pressure mode the diastolic pressure may be zero, but each SBP must exceed its corresponding DBP. Results are numerical measurements, not diagnoses or fluid treatment decisions.

## Important clinical limitations

PPV is a dynamic variable most applicable to controlled mechanical ventilation, adequate ventilatory conditions, and a regular cardiac rhythm. Spontaneous breathing, arrhythmias, low tidal volume, poor arterial waveform fidelity, right ventricular dysfunction, or altered cardiopulmonary mechanics can invalidate commonly used interpretation thresholds. A numerical PPV result **does not by itself establish fluid responsiveness**. The calculator does not derive SVV from PPV. It is intended for research, teaching, and review; it is not a validated medical device.

## Python and API

Python 3.10 or later:

```bash
python -m pip install -e ".[dev]"
python ppv.py ppv --pp-max 42 --pp-min 38
python cli.py ppv --sbp-max 122 --dbp-max 80 --sbp-min 118 --dbp-min 80
python ppv.py batch --input sample_ppv.csv --output results.csv
python -m pytest -q
node --test tests/web.test.mjs
```

Python integration:

```python
from ppv_core import calculate_ppv

result = calculate_ppv(pp_max=42, pp_min=38)
assert result["ppv_percent"] == 10.0
```

To run the optional local FastAPI server:

```bash
AUDIT_SECRET_KEY="replace-with-a-long-random-key" python cli.py serve --host 127.0.0.1
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/api/ppv \
  -H "Content-Type: application/json" \
  -d '{"pp_max":42,"pp_min":38}'
```

The POST `/api/ppv` endpoint returns PPmax, PPmin, PPmean (mmHg) and PPV (%); malformed input returns HTTP 422. OpenAPI documentation is generated at `/docs` when the server runs.

**Existing compatibility interfaces:** The separate legacy `ppv.py single` flow, generic batch routing, and `cli.py audit/chat/batch/verify-audit` remain available. Those legacy generic scores and audit-worker rules are not clinically validated PPV algorithms and should **not** be used for medical decisions. The mock supervisory chat does not perform external inference. The root `index.html` is the standalone PPV application; `web/index.html` links to it.

## Privacy and security

The browser calculator processes values entirely in local JavaScript and generates downloads locally. It does not transmit input data or use browser storage. The optional Python API is a separate server and **is not authenticated**; keep it on trusted local interfaces or add authentication and transport security before exposing it publicly. The API includes a limited regex identifier guard, which is **not a guarantee of de-identification or regulatory compliance**. Do not submit patient identifiers.

The legacy audit log is in-memory. HMAC verification recomputes signatures and checks chain continuity, but it is not durable, independently anchored, or suitable as a regulated audit-record system. Set a strong unique `AUDIT_SECRET_KEY` for deployed servers; the development fallback emits a warning. Docker Compose requires this variable.

## Development and deployment

- Core: Python standard library in `ppv_core.py`; FastAPI/Pydantic only for the optional server; Node.js is used for static-page regression tests.
- Frontend: standalone HTML/CSS/JavaScript. Hosting can use GitHub Pages from the repository root without Python, Pyodide, or a backend.
- CI: Python 3.10–3.12 runs Python unit/integration tests and Node.js browser-script tests.
- Browser compatibility: designed for modern browsers supporting standard JavaScript and Blob downloads; full cross-browser end-to-end testing remains outstanding. No third-party frontend packages.
- License: [MIT](LICENSE).

The GitHub Pages URL comes from repository metadata; availability depends on the repository's Pages settings. Move a verified live-application link directly below the title once publication and an end-to-end smoke test pass.
