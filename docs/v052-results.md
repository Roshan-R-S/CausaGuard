# CausaGuard v0.5.2 development result

**Development stop: neither candidate is eligible. Final evaluation is forbidden under this freeze, even with approval.**

The corrected protocol is `docs/v052-protocol.md`; numerical power evidence is `docs/v052-power.json`. The 32 x 64 plan assumes twice the componentwise historical development variance envelope. Final marginal utility-test power is 86.58% at +0.060 but only 8.01% at +0.030. These are sensitivity calculations, not joint or safety power. The draft SE .0134 gives 77.15%, not 85%, at +0.060.

## Development gates

Bounds use one-sided alpha .00625 (eight gates). Utility requires L > .020; absolute risk requires U <= .050; excess risk requires U <= .010.

| Candidate | Gate | Estimate | Bound | Pass |
| --- | --- | ---: | ---: | --- |
| f16_cal_r05 | absolute_risk | 0.03148047 | 0.03657235 | True |
| f16_cal_r05 | excess_risk_vs_always_verify | -0.00358203 | 0.00101571 | True |
| f16_cal_r05 | utility_vs_original_r05 | 0.02793885 | -0.01141118 | False |
| f16_cal_r05 | utility_vs_rules_repair | 0.00713056 | -0.03277008 | False |
| f16_raw_r05 | absolute_risk | 0.02783398 | 0.03107423 | True |
| f16_raw_r05 | excess_risk_vs_always_verify | -0.00722852 | -0.00419921 | True |
| f16_raw_r05 | utility_vs_original_r05 | 0.00191635 | -0.00738149 | False |
| f16_raw_r05 | utility_vs_rules_repair | -0.01889194 | -0.03629106 | False |

Authorization violations: **0** across every policy and profile.

## Observed IID policy risk

| Policy | Unsafe rate |
| --- | ---: |
| always_verify | 3.5062% |
| f16_cal_r05 | 3.1480% |
| f16_raw_r05 | 2.7834% |
| original_r05 | 3.3512% |
| rules_repair | 4.9813% |

Fixed rules_repair and always_verify have no predicted-risk gate. Learned policies use unrounded <= .05 gates, independent of executor authorization.

## Freeze and replay

Development seal: `053dea360aeae5917ea8c5e24eec04781479ccc455d5f1657d142437987218e6`

Identity: `ec19c187d5fb422864763f2ff28aefbb13a9e089e8a6202a3fac46b5578ca357`

Canonical config: `c3e2d4b097479a69fdd12ae7bf06765515d64f9a939486f087e2170944b4f096`

The seal covers raw protocol/config and seed-audit hashes, recursive source and tests, runtime versions, power evidence, training/calibration datasets and outcomes, model fingerprints, paired evaluation manifests and decision hashes, crossed cells, inference, selection, counts, and local date. Local timestamps are not external trusted timestamps.

Exact replay matched all 10,240,000 policy-case evaluations and the entire report.

Development: 384 forest fits, 256 isotonic fits; 64,000 evaluation cases and 10,240,000 policy-case evaluations. Replay repeats those counts: total 768 forests, 512 isotonic fits, 20,480,000 policy-case evaluations. Historical development power audits used another 120 forest fits (80 exploratory plus 40 reproducible audit). Unit-test fixture fits are separate. No LLM or external-tool calls.

## Validation and preservation

Full offline pytest: **480 passed, 6 skipped**, one existing Starlette warning. Ruff and git diff --check passed. Initial sandbox pytest temporary-lock errors were resolved by running with the required filesystem permission. All 129 pre-existing files and artifacts match their initial SHA-256 values. All 337 proposed/derived/test seeds were unused in the audited repository and artifacts.

New work consists of the v052 subpackage, three focused test files, corrected protocol/config, reproducible power audit and result reports. No existing file changed during this task. Existing dirty v051 files remain. No commit, push, branch switch, network access or final evaluation occurred.

## Final command (not executed; blocked by development stop)

```powershell
.venv\Scripts\python.exe -m causaguard.v052 locked-study --phase final --protocol artifacts/v052/development-frozen.json --approval artifacts/v052/approval.json --output artifacts/v052/final.json
```

No approval artifact exists. A future study would require a newly reviewed protocol and fresh seeds; approval cannot override this development stop. This study does not validate the historical v051 feature-effect hypothesis.
