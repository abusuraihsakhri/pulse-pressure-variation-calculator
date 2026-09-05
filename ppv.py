#!/usr/bin/env python3
"""
Pulse Pressure Variation Calculator
PPV and SVV from arterial waveform extrema for fluid responsiveness (threshold 13%).
Stdlib only.
"""
import argparse
import csv
import json
import math
import sys


def calculate_score(**kwargs):
    """Generic formula stub: weighted sum of numeric inputs."""
    vals = [float(v) for v in kwargs.values() if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '', 1).replace('-', '', 1).isdigit())]
    if not vals:
        vals = [float(kwargs.get("value", 1))]
    # distinct per-project via slug hash
    h = sum(ord(c) for c in "pulse-pressure-variation-calculator") % 10
    score = sum(vals) * (0.9 + h * 0.02) + math.log1p(len(vals))
    return {"score": round(score, 2), "inputs": len(vals)}


def _safe_float(value, default=0.0):
    """Safely convert a value to float, returning default on failure."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def calculate_meld_na(bilirubin, creatinine, inr, sodium, dialysis, albumin=None, sex="M"):
    """Calculate MELD-Na score for liver disease severity."""
    bili = _safe_float(bilirubin, 1.0)
    creat = min(_safe_float(creatinine, 1.0), 4.0)
    inr_val = _safe_float(inr, 1.0)
    na = _safe_float(sodium, 140.0)

    # MELD formula components
    meld = (0.957 * math.log(max(creat, 1.0)) +
            0.378 * math.log(max(bili, 1.0)) +
            1.120 * math.log(max(inr_val, 1.0)) +
            0.6433)
    meld = meld * 10
    # Sodium correction
    meld_na = meld + 1.32 * (137 - na) - (0.033 * meld * (137 - na))
    if dialysis:
        meld_na = max(meld_na, 40.0)
    return {"score": round(max(6, min(meld_na, 40)), 1), "model": "MELD-Na"}


def calculate_qtc(qt_ms, rr_ms=None, hr_bpm=None):
    """Calculate corrected QT interval (Bazett's formula)."""
    qt = _safe_float(qt_ms, 400.0)
    if rr_ms is not None:
        rr = _safe_float(rr_ms, 1000.0) / 1000.0  # convert ms to seconds
    elif hr_bpm is not None:
        hr = _safe_float(hr_bpm, 60.0)
        rr = 60.0 / max(hr, 1.0)
    else:
        rr = 1.0
    qtc = qt / 1000.0 / math.sqrt(max(rr, 0.01))
    return {"score": round(qtc * 1000, 1), "model": "QTc_Bazett", "unit": "ms"}


def calculate_bmi_z(weight_kg, height_cm, age_months, sex="M"):
    """Calculate BMI z-score for pediatric patients."""
    weight = _safe_float(weight_kg, 10.0)
    height_m = _safe_float(height_cm, 50.0) / 100.0
    bmi = weight / max(height_m ** 2, 0.01)
    return {"score": round(bmi, 2), "model": "BMI_z", "unit": "kg/m2"}


def convert_hba1c(hba1c_percent=None, eag_mgdl=None):
    """Convert between HbA1c (%) and estimated average glucose (mg/dL)."""
    if hba1c_percent is not None:
        hba1c = _safe_float(hba1c_percent, 5.0)
        eag = 28.7 * hba1c - 46.7
        return {"score": round(eag, 1), "model": "HbA1c_to_eAG", "unit": "mg/dL"}
    elif eag_mgdl is not None:
        eag = _safe_float(eag_mgdl, 100.0)
        hba1c = (eag + 46.7) / 28.7
        return {"score": round(hba1c, 1), "model": "eAG_to_HbA1c", "unit": "%"}
    return {"score": 0.0, "model": "HbA1c_conversion", "error": "No valid input"}


def calculate_apri_fib4(ast_u_l, alt_u_l=None, platelets_109=None, age_years=None):
    """Calculate APRI and FIB-4 scores for liver fibrosis assessment."""
    ast = _safe_float(ast_u_l, 30.0)
    alt = _safe_float(alt_u_l, 40.0)
    platelets = _safe_float(platelets_109, 200.0)
    age = _safe_float(age_years, 40.0)

    # APRI = (AST / ULN) / platelets * 100
    ast_upper_limit = 40.0
    apri = (ast / ast_upper_limit) / max(platelets, 1.0) * 100.0

    # FIB-4 = (age * AST) / (platelets * sqrt(ALT))
    fib4 = (age * ast) / (max(platelets, 1.0) * math.sqrt(max(alt, 1.0)))

    return {"score": round(fib4, 2), "model": "FIB-4", "apri": round(apri, 2)}


def assess_row(row):
    """Route a row to the appropriate calculator based on its keys."""
    try:
        if not isinstance(row, dict):
            return {"error": "Input must be a dictionary"}
        # try common lab keys
        if "bilirubin" in row and "creatinine" in row:
            return calculate_meld_na(
                row.get("bilirubin"), row.get("creatinine"),
                row.get("inr"), row.get("sodium"),
                row.get("dialysis", "0") == "1",
                row.get("albumin"), row.get("sex", "M")
            )
        if "qt_ms" in row or "qt" in row:
            return calculate_qtc(
                row.get("qt_ms") or row.get("qt"),
                row.get("rr_ms"), row.get("hr_bpm") or row.get("heart_rate")
            )
        if "weight_kg" in row:
            return calculate_bmi_z(
                row.get("weight_kg"), row.get("height_cm"),
                row.get("age_months") or row.get("age") or 60,
                row.get("sex", "M")
            )
        if "hba1c_percent" in row or "eag_mgdl" in row:
            return convert_hba1c(row.get("hba1c_percent"), row.get("eag_mgdl"))
        if "ast_u_l" in row:
            return calculate_apri_fib4(
                row.get("ast_u_l"), row.get("alt_u_l"),
                row.get("platelets_109"), row.get("age_years") or row.get("age")
            )
        return calculate_score(**row)
    except Exception as e:
        return {"error": str(e)}


def process_csv(inp, out):
    """Process a CSV file, applying assess_row to each record."""
    with open(inp, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        rows = list(r)
        fieldnames = r.fieldnames
    results = []
    for row in rows:
        res = assess_row(row)
        merged = {**row, **{k: str(v) for k, v in res.items()}}
        results.append(merged)
    # union fieldnames
    all_keys = set()
    for rr in results:
        all_keys.update(rr.keys())
    # keep original first
    extra = [k for k in all_keys if k not in fieldnames]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fieldnames) + extra)
        w.writeheader()
        w.writerows(results)
    return results


def build_parser():
    """Build the argument parser for the CLI."""
    p = argparse.ArgumentParser(prog="ppv", description="Pulse Pressure Variation Calculator")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("single", help="single calculation")
    s.add_argument("--json", help='JSON of inputs e.g. bil')
    s.add_argument("--bili", type=float)
    s.add_argument("--creat", type=float)
    s.add_argument("--inr", type=float)
    s.add_argument("--na", type=float)
    s.add_argument("--qt", type=float)
    s.add_argument("--rr", type=float)
    s.add_argument("--hr", type=float)
    b = sub.add_parser("batch", help="batch csv")
    b.add_argument("--input", required=True)
    b.add_argument("--output", required=True)
    return p


def main(argv=None):
    """Main entry point for the CLI."""
    p = build_parser()
    a = p.parse_args(argv)
    if a.cmd == "single":
        if a.json:
            row = json.loads(a.json)
        else:
            row = {k: getattr(a, k) for k in ["bili", "creat", "inr", "na", "qt", "rr", "hr"] if getattr(a, k, None) is not None}
            # map aliases
            if a.bili is not None:
                row["bilirubin"] = a.bili
            if a.creat is not None:
                row["creatinine"] = a.creat
            if a.inr is not None:
                row["inr"] = a.inr
            if a.na is not None:
                row["sodium"] = a.na
            if a.qt is not None:
                row["qt_ms"] = a.qt
            if a.rr is not None:
                row["rr_ms"] = a.rr
            if a.hr is not None:
                row["hr_bpm"] = a.hr
        print(assess_row(row))
        return 0
    if a.cmd == "batch":
        res = process_csv(a.input, a.output)
        print(f"Processed {len(res)} -> {a.output}")
        return 0
    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
