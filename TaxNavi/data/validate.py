#!/usr/bin/env python3
"""Check tax-parameters-v1.json before publishing.

Mirrors TaxParameterValidator in the app: if this passes, the app will
accept the file. Usage:  python3 validate.py [path]   (default: the v1 file)
"""
import json
import sys
from pathlib import Path

SCHEMA_VERSION = 1
errors = []


def fail(msg):
    errors.append(msg)


def is_rate(v):
    return isinstance(v, (int, float)) and 0 <= v <= 1


def positive(v):
    return isinstance(v, (int, float)) and v > 0


def bound(v):
    """null = no upper bound."""
    return float("inf") if v is None else v


def ascending(values, name):
    vals = [bound(v) for v in values]
    if not vals or any(a >= b for a, b in zip(vals, vals[1:])):
        fail(f"{name}: upperBound must be non-empty and ascending")


def open_ended(values, name):
    if not values or values[-1] is not None:
        fail(f"{name}: the last band must have upperBound null")


def check_tax(t, year):
    ascending([b["upperBound"] for b in t["employmentDeductionBrackets"]], f"{year} employmentDeductionBrackets")
    for key in ("incomeTaxBasicDeductionBrackets", "residentTaxBasicDeductionBrackets", "incomeTaxBrackets"):
        ups = [b["upperBound"] for b in t[key]]
        ascending(ups, f"{year} {key}")
        open_ended(ups, f"{year} {key}")
    for b in t["incomeTaxBrackets"]:
        if not is_rate(b["rate"]):
            fail(f"{year} incomeTaxBrackets rate {b['rate']} is not a rate")
    for b in t["employmentDeductionBrackets"]:
        if b["rate"] != 1 and not is_rate(b["rate"]):
            fail(f"{year} employment rate {b['rate']} is not a rate")
    for key in ("reconstructionSurtaxRate", "residentIncomeLevyRate"):
        if not is_rate(t[key]):
            fail(f"{year} {key} is not a rate")
    if not positive(t["employmentDeductionCap"]):
        fail(f"{year} employmentDeductionCap must be positive")


def check_deductions(d, year):
    if not positive(d["dependentIncomeLimit"]):
        fail(f"{year} dependentIncomeLimit must be positive")
    if not (d["dependentIncomeLimit"] < d["specificRelativeIncomeLimit"]
            and d["dependentIncomeLimit"] < d["spouseSpecialIncomeLimit"]):
        fail(f"{year} income limits out of order")
    ascending([r["upperBound"] for r in d["spouseSpecialTable"]], f"{year} spouseSpecialTable")
    ascending([r["upperBound"] for r in d["specificRelativeTable"]], f"{year} specificRelativeTable")
    for r in d["spouseSpecialTable"]:
        if len(r["income"]) != 3 or len(r["resident"]) != 3:
            fail(f"{year} spouseSpecialTable rows need three columns")
    for key in ("medicalIncomeRate", "donationResidentBasicRate", "donationSpecialCapRate"):
        if not is_rate(d[key]):
            fail(f"{year} {key} is not a rate")


def check_social(s):
    if not 0.05 <= s["nationalHealthRate"] <= 0.15:
        fail("nationalHealthRate out of range (5-15%)")
    prefs = s["prefectureHealthRates"]
    if len(prefs) != 47 or len({p["name"] for p in prefs}) != 47:
        fail("prefectureHealthRates must list 47 prefectures")
    for p in prefs:
        if not 0.05 <= p["totalRate"] <= 0.15:
            fail(f"health rate for {p['name']} out of range")
    if not (0 <= s["careRate"] < 0.05 and 0 <= s["childSupportRate"] < 0.02
            and 0.1 <= s["pensionRate"] <= 0.25 and 0 <= s["employmentInsuranceWorkerRate"] < 0.02):
        fail("a social insurance rate is out of range")
    for key in ("healthMonthlyCap", "pensionMonthlyCap", "standardMonthlyFloor", "pensionBonusCapPerPayment",
                "healthBonusCapAnnual", "nationalPensionMonthly", "dependentIncomeCeiling", "basicPensionFullAnnual"):
        if not positive(s[key]):
            fail(f"{key} must be positive")
    for key in ("nhiIncomeRate", "pensionAccrualRate"):
        if not is_rate(s[key]):
            fail(f"{key} is not a rate")


def check_employment(e):
    leave = e["leave"]
    if not positive(leave["childcareWageMonthlyCap"]) or leave["childcareWageMonthlyFloor"] >= leave["childcareWageMonthlyCap"]:
        fail("childcare wage floor/cap out of order")
    for key in ("childcareRateHigh", "childcareRateLow", "postBirthSupportRate", "maternityRate"):
        if not is_rate(leave[key]):
            fail(f"leave {key} is not a rate")
    u = e["unemployment"]
    if len(u["wageDailyCaps"]) != 4 or len(u["dailyBenefitCaps"]) != 4:
        fail("unemployment caps need four age bands (<30, 30-44, 45-59, 60-64)")
    elif not (u["wageDailyFloor"] > 0 and u["rateTaperStart"] < u["rateTaperEnd60to64"] <= u["rateTaperEndUnder60"]
              and all(0 < d < w for d, w in zip(u["dailyBenefitCaps"], u["wageDailyCaps"]))):
        fail("unemployment figures out of order")


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("tax-parameters-v1.json")
    try:
        p = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"NG: cannot read {path}: {e}")
        return 1
    try:
        if p["schemaVersion"] != SCHEMA_VERSION:
            fail(f"schemaVersion {p['schemaVersion']} is not {SCHEMA_VERSION}")
        if not p["dataVersion"]:
            fail("dataVersion is empty")
        if str(p["currentIncomeYear"]) not in p["incomeYears"]:
            fail(f"no incomeYears entry for currentIncomeYear {p['currentIncomeYear']}")
        for year, rules in p["incomeYears"].items():
            if not year.isdigit():
                fail(f"income year key {year} is not a year")
            check_tax(rules["tax"], year)
            check_deductions(rules["deductions"], year)
        check_social(p["socialInsurance"])
        check_employment(p["employmentInsurance"])
    except KeyError as e:
        fail(f"missing field {e}")
    if errors:
        print("NG:")
        for e in errors:
            print("  -", e)
        return 1
    print(f"OK: dataVersion {p['dataVersion']}, currentIncomeYear {p['currentIncomeYear']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
