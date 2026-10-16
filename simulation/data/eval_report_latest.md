# Aegis Red-Team Evaluation Report (AEG-61)

**Run Timestamp:** 2026-10-12T21:27:22.289259+00:00
**Status:** [PASS] PASSED
**Total Cases Evaluated:** 200

---

## 1. Key Performance Indicators (KPIs)

| Metric | Measured Value | Operational Target | Status |
|:-------|:--------------:|:------------------:|:------:|
| **Accuracy** | **100.0%** | > 98.0 % | PASS |
| **False Positive Rate (FPR)** | **0.0%** | < 1.5 % | PASS |
| **Recall / Fraud Detection** | **100.0%** | > 97.0 % | PASS |
| **Average Latency** | **323.07 ms** | < 2,800 ms | PASS |
| **p95 Latency** | **552.35 ms** | < 4,000 ms | PASS |

---

## 2. Confusion Matrix

```
                      PREDICTED FRAUD     PREDICTED BENIGN
ACTUAL FRAUD (500)            48 (TP)               0 (FN)
ACTUAL BENIGN (1500)           0 (FP)             152 (TN)
```

---

## 3. Policy and Determinism Verification

- **Hard-rule floors:** Verified. Tor ATO bounds threat score >= 85 and locks account.
- **Structuring:** Smurfing velocity bursts bounds threat score >= 75 and blocks transaction.
- **Clean triage:** Benign transactions bypass LLM inference in fast-path triage (< 1.0s).
- **LLM bounds:** Score adjustment strictly clamped within [-10, +10].
