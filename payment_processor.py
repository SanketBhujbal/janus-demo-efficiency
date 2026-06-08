"""
janus-demo-efficiency/payment_processor.py
Payments domain module — intentionally inefficient.
DO NOT USE IN PRODUCTION.

Designed for the JANUS efficiency demo:
  Finding 0 → find_flagged_account_ids    → VERIFIED   (O(n²) → O(n) set lookup)
  Finding 1 → build_settlement_csv        → VERIFIED   (O(n²) string concat → join)
  Finding 2 → detect_duplicate_charge_pairs → FAILED   (semantics change — see note)
"""
from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Pattern 1: O(n²) — `in list` probe inside a loop.
# Fix: convert flagged_ids to a set once, check membership in O(1).
# Rule: efficiency.linear-search-in-loop
# ---------------------------------------------------------------------------
def find_flagged_account_ids(
    all_account_ids: list,
    flagged_ids: list,
) -> list:
    """Return account IDs that appear on the fraud / blocked list."""
    result = []
    for account_id in all_account_ids:
        if account_id in flagged_ids:       # O(n) list scan per probe -> O(n*m) total
            result.append(account_id)
    return result


# ---------------------------------------------------------------------------
# Pattern 2: O(n²) memory — string concatenation inside a loop.
# Fix: collect rows in a list, join once at the end.
# Rule: efficiency.string-concat-in-loop
# ---------------------------------------------------------------------------
def build_settlement_csv(rows: list) -> str:
    """Serialize a settlement batch to CSV for the clearing house."""
    report = ""
    for row in rows:
        report += ",".join(str(field) for field in row) + "\n"  # new string object each iteration
    return report


# ---------------------------------------------------------------------------
# Pattern 3: O(n²) — nested loop over the same charges list.
#
# NOTE: This function intentionally returns BOTH directions of each pair —
#   (chg_a.id, chg_b.id) AND (chg_b.id, chg_a.id) — matching the existing
#   downstream consumer that de-duplicates at the caller level.
# Any optimization that groups by key produces each pair only once,
# changing the contract → JANUS correctly REJECTS it (output mismatch).
# This demonstrates the safety net: JANUS never applies a refactoring that
# changes observable behaviour, even if it looks faster.
#
# Rule: efficiency.nested-loop-same-iterable
# ---------------------------------------------------------------------------
def detect_duplicate_charge_pairs(
    charges: list,
) -> list:
    """Detect potentially duplicate charge submissions.

    Returns both (a, b) and (b, a) for each matching pair — callers rely
    on this bidirectional output for their own dedup logic.
    """
    pairs = []
    for chg_a in charges:
        for chg_b in charges:               # O(n²) — iterates full list per charge
            if chg_a is chg_b:
                continue
            if (chg_a["merchant_id"] == chg_b["merchant_id"]
                    and chg_a["amount"] == chg_b["amount"]):
                pairs.append((chg_a["id"], chg_b["id"]))
    return pairs   # intentionally bidirectional: includes (a,b) AND (b,a)


# ---------------------------------------------------------------------------
# Pattern 4: O(n) redundant regex compiles — re-compiling inside the loop.
# Fix: call re.compile() once before the loop.
# Rule: efficiency.regex-recompile-in-loop
# (Included for scan completeness; capped by max_findings=3 in demo mode.)
# ---------------------------------------------------------------------------
def mask_card_numbers_in_audit_log(lines: list) -> list:
    """Mask card PANs in audit log lines for PCI-DSS compliance."""
    masked = []
    for line in lines:
        pan_pattern = r"\b(\d{6})\d{6}(\d{4})\b"      # compiled fresh every iteration
        masked.append(re.sub(pan_pattern, r"\1XXXXXX\2", line))
    return masked


# ---------------------------------------------------------------------------
# sample_inputs() — used by the JANUS benchmark driver.
#
# Sizing rationale:
#   find_flagged_account_ids : 5k × 3k list probe   → ~180ms/call  → 5.4s / 30 iters ✓
#   build_settlement_csv     : 1500 rows concat      → ~80ms/call   → 2.4s / 30 iters ✓
#   detect_duplicate_charge_pairs: 1500 charges      → ~180ms/call  → 5.4s / 30 iters ✓
#   mask_card_numbers        : 50k log lines compile → ~200ms/call  → 6s / 30 iters   ✓
# ---------------------------------------------------------------------------
def sample_inputs() -> dict:
    # Pattern 1: 5,000 accounts vs 3,000 flagged IDs (list, not set — the bug)
    all_account_ids = list(range(500, 5_500))          # 5,000 items
    flagged_ids     = list(range(0, 3_000))            # 3,000 items — list, not set

    # Pattern 2: 1,500 settlement rows (sized so 30 bench iters complete < 5s)
    rows = [
        [
            f"settle-{i:05d}",
            f"acct-{i % 500:04d}",
            f"{(i % 99) * 1.25:.2f}",
            "USD",
            "2026-01-15",
            "COMPLETED",
        ]
        for i in range(1_500)
    ]

    # Pattern 3: 1,500 charges — O(n²) = 2.25M comparisons, ~180ms/call
    charges = [
        {
            "id":          f"chg-{i:05d}",
            "merchant_id": i % 200,
            "amount":      round((i % 23) * 0.50, 2),
        }
        for i in range(1_500)
    ]

    # Pattern 4: 50,000 log lines (for regex compile demo)
    lines = [
        f"2026-01-15 12:{i % 60:02d}:{i % 60:02d} CHARGE "
        f"pan=4111{(i * 7) % 10**12:012d} cvv={(i * 3) % 1000:03d} "
        f"amount={i * 0.01:.2f} status=OK"
        for i in range(50_000)
    ]

    return {
        "find_flagged_account_ids":       (all_account_ids, flagged_ids),
        "build_settlement_csv":           (rows,),
        "detect_duplicate_charge_pairs":  (charges,),
        "mask_card_numbers_in_audit_log": (lines,),
    }


if __name__ == "__main__":
    inputs = sample_inputs()
    for name, args in inputs.items():
        func = globals()[name]
        result = func(*args)
        print(f"{name}: ok  len={len(result)}")
