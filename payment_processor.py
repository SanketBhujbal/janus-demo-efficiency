"""
janus-demo-efficiency/payment_processor.py
Payments domain module — intentionally inefficient.
DO NOT USE IN PRODUCTION.

Each function maps 1:1 to a JANUS Semgrep efficiency rule:
  1. find_flagged_account_ids       -> efficiency.linear-search-in-loop      O(n²) -> O(n)
  2. detect_duplicate_charge_pairs  -> efficiency.nested-loop-same-iterable  O(n²) -> O(n)
  3. build_settlement_csv           -> efficiency.string-concat-in-loop      O(n²) -> O(n)
  4. mask_card_numbers_in_audit_log -> efficiency.regex-recompile-in-loop    O(n) compiles -> 1
"""
from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Pattern 1: O(n²) — `in list` probe inside a loop.
# Fix: convert flagged_ids to a set once, check membership in O(1).
# ---------------------------------------------------------------------------
def find_flagged_account_ids(
    all_account_ids: list[int],
    flagged_ids: list[int],
) -> list[int]:
    """Return account IDs that appear on the fraud / blocked list."""
    result = []
    for account_id in all_account_ids:
        if account_id in flagged_ids:       # O(n) list scan per probe -> O(n*m) total
            result.append(account_id)
    return result


# ---------------------------------------------------------------------------
# Pattern 2: O(n²) — nested loop over the same charges list.
# Fix: group by (merchant_id, amount) in a dict, compare within groups.
# ---------------------------------------------------------------------------
def detect_duplicate_charge_pairs(
    charges: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    """Detect potentially fraudulent duplicate charge submissions."""
    pairs = []
    for chg_a in charges:
        for chg_b in charges:               # iterates entire list for every charge -> O(n²)
            if chg_a is chg_b:
                continue
            if (chg_a["merchant_id"] == chg_b["merchant_id"]
                    and chg_a["amount"] == chg_b["amount"]):
                pairs.append((chg_a["id"], chg_b["id"]))
    return pairs


# ---------------------------------------------------------------------------
# Pattern 3: O(n²) memory — string concatenation inside a loop.
# Fix: collect rows in a list, join once at the end.
# ---------------------------------------------------------------------------
def build_settlement_csv(rows: list[list[Any]]) -> str:
    """Serialize a settlement batch to CSV for the clearing house."""
    report = ""
    for row in rows:
        report += ",".join(str(field) for field in row) + "\n"  # new string object each iteration
    return report


# ---------------------------------------------------------------------------
# Pattern 4: O(n) redundant regex compiles — re-compiling inside the loop.
# Fix: call re.compile() once before the loop and reuse the compiled object.
# ---------------------------------------------------------------------------
def mask_card_numbers_in_audit_log(lines: list[str]) -> list[str]:
    """Mask card PANs in audit log lines for PCI-DSS compliance."""
    masked = []
    for line in lines:
        pan_pattern = r"\b(\d{6})\d{6}(\d{4})\b"      # compiled fresh every iteration
        masked.append(re.sub(pan_pattern, r"\1XXXXXX\2", line))
    return masked


# ---------------------------------------------------------------------------
# sample_inputs() — used by the JANUS benchmark driver.
# Sized so each function runs 50-500 ms (fits 30 iterations in < 20 s).
# ---------------------------------------------------------------------------
def sample_inputs() -> dict:
    # Pattern 1: 5,000 accounts vs 3,000 flagged IDs (kept as list for O(n) probe)
    all_account_ids = list(range(500, 5_500))          # 5 000 items
    flagged_ids     = list(range(0, 3_000))            # 3 000 items — list, not set

    # Pattern 2: 2,000 charges -> 4 M comparisons in the nested loop
    charges = [
        {
            "id":          f"chg-{i:05d}",
            "merchant_id": i % 200,
            "amount":      round((i % 23) * 0.50, 2),
        }
        for i in range(2_000)
    ]

    # Pattern 3: 3,000 settlement rows x 6 fields
    rows = [
        [
            f"settle-{i:05d}",
            f"acct-{i % 500:04d}",
            f"{(i % 99) * 1.25:.2f}",
            "USD",
            "2026-01-15",
            "COMPLETED",
        ]
        for i in range(3_000)
    ]

    # Pattern 4: 50,000 log lines — amplifies the compile overhead to visible levels
    lines = [
        f"2026-01-15 12:{i % 60:02d}:{i % 60:02d} CHARGE "
        f"pan=4111{(i * 7) % 10**12:012d} cvv={(i * 3) % 1000:03d} "
        f"amount={i * 0.01:.2f} status=OK"
        for i in range(50_000)
    ]

    return {
        "find_flagged_account_ids":       (all_account_ids, flagged_ids),
        "detect_duplicate_charge_pairs":  (charges,),
        "build_settlement_csv":           (rows,),
        "mask_card_numbers_in_audit_log": (lines,),
    }


if __name__ == "__main__":
    inputs = sample_inputs()
    for name, args in inputs.items():
        func = globals()[name]
        result = func(*args)
        print(f"{name}: ok  len={len(result)}")
