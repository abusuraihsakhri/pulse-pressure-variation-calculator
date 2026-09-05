"""
Focused tests for ppv.py core calculator functions.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import ppv


class TestCalculateScore:
    def test_basic_score(self):
        result = ppv.calculate_score(value=10, qty=2)
        assert isinstance(result, dict)
        assert "score" in result
        assert "inputs" in result
        assert result["inputs"] == 2

    def test_empty_inputs(self):
        result = ppv.calculate_score()
        assert isinstance(result, dict)
        assert result["inputs"] == 1

    def test_string_numeric_values(self):
        result = ppv.calculate_score(a="5.5", b="3.2")
        assert result["inputs"] == 2
        assert result["score"] > 0


class TestMeldNa:
    def test_basic_meld(self):
        result = ppv.calculate_meld_na(
            bilirubin=2.5, creatinine=1.2, inr=1.1, sodium=138, dialysis=False
        )
        assert "score" in result
        assert result["model"] == "MELD-Na"
        assert 6 <= result["score"] <= 40

    def test_dialysis_cap(self):
        result = ppv.calculate_meld_na(
            bilirubin=0.5, creatinine=0.5, inr=1.0, sodium=140, dialysis=True
        )
        assert result["score"] >= 6

    def test_none_values(self):
        result = ppv.calculate_meld_na(
            bilirubin=None, creatinine=None, inr=None, sodium=None, dialysis=False
        )
        assert "score" in result


class TestQTc:
    def test_qtc_with_hr(self):
        result = ppv.calculate_qtc(qt_ms=420, hr_bpm=72)
        assert result["model"] == "QTc_Bazett"
        assert result["unit"] == "ms"
        assert result["score"] > 0

    def test_qtc_with_rr(self):
        result = ppv.calculate_qtc(qt_ms=400, rr_ms=1000)
        assert result["score"] > 0

    def test_qtc_defaults(self):
        result = ppv.calculate_qtc(qt_ms=400)
        assert "score" in result


class TestBMIZ:
    def test_basic_bmi(self):
        result = ppv.calculate_bmi_z(weight_kg=70, height_cm=175, age_months=120)
        assert result["model"] == "BMI_z"
        assert result["unit"] == "kg/m2"
        assert result["score"] > 0

    def test_none_values(self):
        result = ppv.calculate_bmi_z(weight_kg=None, height_cm=None, age_months=None)
        assert "score" in result


class TestHbA1c:
    def test_hba1c_to_eag(self):
        result = ppv.convert_hba1c(hba1c_percent=7.0)
        assert result["model"] == "HbA1c_to_eAG"
        assert result["unit"] == "mg/dL"
        assert result["score"] > 0

    def test_eag_to_hba1c(self):
        result = ppv.convert_hba1c(eag_mgdl=154.0)
        assert result["model"] == "eAG_to_HbA1c"
        assert result["unit"] == "%"
        assert result["score"] > 0

    def test_no_input(self):
        result = ppv.convert_hba1c()
        assert "error" in result


class TestAPRIFIB4:
    def test_basic_fib4(self):
        result = ppv.calculate_apri_fib4(
            ast_u_l=45, alt_u_l=50, platelets_109=200, age_years=45
        )
        assert result["model"] == "FIB-4"
        assert "apri" in result
        assert result["score"] > 0

    def test_none_values(self):
        result = ppv.calculate_apri_fib4(ast_u_l=30)
        assert "score" in result


class TestAssessRow:
    def test_meldna_routing(self):
        result = ppv.assess_row({"bilirubin": 2.0, "creatinine": 1.0, "inr": 1.0, "sodium": 140})
        assert result["model"] == "MELD-Na"

    def test_qtc_routing(self):
        result = ppv.assess_row({"qt_ms": 400, "hr_bpm": 60})
        assert result["model"] == "QTc_Bazett"

    def test_bmi_routing(self):
        result = ppv.assess_row({"weight_kg": 70, "height_cm": 175, "age": 120})
        assert result["model"] == "BMI_z"

    def test_hba1c_routing(self):
        result = ppv.assess_row({"hba1c_percent": 7.0})
        assert "model" in result

    def test_apri_routing(self):
        result = ppv.assess_row({"ast_u_l": 40})
        assert result["model"] == "FIB-4"

    def test_generic_fallback(self):
        result = ppv.assess_row({"value": 10, "qty": 2})
        assert "score" in result

    def test_invalid_input(self):
        result = ppv.assess_row("not a dict")
        assert "error" in result


class TestProcessCSV:
    def test_process_sample_csv(self, tmp_path):
        input_csv = tmp_path / "input.csv"
        output_csv = tmp_path / "output.csv"
        input_csv.write_text("id,value,qty\nA,10,2\nB,20,3\n")

        results = ppv.process_csv(str(input_csv), str(output_csv))
        assert len(results) == 2
        assert output_csv.exists()

    def test_process_meldna_csv(self, tmp_path):
        input_csv = tmp_path / "input.csv"
        output_csv = tmp_path / "output.csv"
        input_csv.write_text("bilirubin,creatinine,inr,sodium\n2.0,1.0,1.0,140\n")

        results = ppv.process_csv(str(input_csv), str(output_csv))
        assert len(results) == 1
        assert "model" in results[0]
