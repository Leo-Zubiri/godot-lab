# h06 matrix results (A / A' / B, N=5 each) — EXPLORATORY

**No statistical-significance claim (N=5).** Quality (blind evaluator), practical_validity (objective GUT), and provenance are reported SEPARATELY.

| metric | A | A' | B |
|---|---|---|---|
| n | 5 | 5 | 5 |
| GUT PASS (practical validity) | 0 | 3 | 5 |
| practical_validity mean | 0 | 1.8 | 3 |
| quality overall mean (blind) | 2.289 | 2.422 | 2.422 |
| mean knowledge reads | 0 | 0 | 3.2 |
| runs citing references | 3 | 0 | 5 |

## Blind quality means per dimension
| dimension | A | A' | B |
|---|---|---|---|
| technical_correctness | 2.6 | 3 | 3 |
| api_correctness | 3 | 3 | 3 |
| version_compatibility | 3 | 3 | 3 |
| architectural_quality | 2.4 | 2.6 | 2.8 |
| requirement_fulfillment | 2.6 | 2.8 | 3 |
| source_quality | 0.6 | 0.8 | 1 |
| provenance | 0.4 | 1 | 1 |
| hallucinations | 3 | 2.6 | 2 |
| clarity | 3 | 3 | 3 |

## Caveats
- N=5 per condition is EXPLORATORY; no statistical significance.
- Generator and evaluator are both Anthropic models (not provider-independent).
- practical_validity is objective (GUT); quality is blind-evaluator; provenance is separate — never combined.
- A' is an instruction+empty-dir placebo; see mean_knowledge_reads for A' retrieval attempts.
