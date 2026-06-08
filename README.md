# JANUS Demo — Efficiency Mission

A seeded Python payments processor used to demonstrate JANUS's autonomous
**profile → refactor → benchmark → $/yr savings** efficiency loop.

## Seeded inefficiencies

| # | Function | Rule | Pattern | Complexity | Expected speedup |
|---|---|---|---|---|---|
| 1 | `find_flagged_account_ids` | `linear-search-in-loop` | `x in list` inside loop | O(n²) → O(n) | ~200× |
| 2 | `detect_duplicate_charge_pairs` | `nested-loop-same-iterable` | double `for chg in charges` | O(n²) → O(n) | ~120× |
| 3 | `build_settlement_csv` | `string-concat-in-loop` | `report += row` in loop | O(n²) → O(n) | ~150× |
| 4 | `mask_card_numbers_in_audit_log` | `regex-recompile-in-loop` | `re.compile()` in loop | O(n) → O(1) compile | ~30× |

## Demo settings (webapp)

| Field | Value |
|---|---|
| **Repository path** | `C:\Users\bhujbalsa\janus-demo-efficiency` |
| **Mode** | `Efficiency: Full loop — refactor → verify → savings` |
| **Calls / year** | `500000000` *(500M — enterprise payments volume)* |
| **CPU $/hour** | `0.272` *(c6g.2xlarge — typical compute)* |
| **Grid region** | `EU-27 (251 g)` |

## Expected results

- 4 findings scanned → 4 refactored → 3-4 verified
- Combined annual savings: **~$5,000–$13,000/yr**
- CO₂ avoided: **~500–1,200 kg/yr**
- Runs in ~3-4 minutes with Claude Code login
