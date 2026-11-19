# Experiment plan (training intentionally pending)

## Single-model scope

Use only `google/gemma-3-270m-it`. No second model and no from-scratch baseline.

## Data arms

1. Human-only: moves from higher-rated Lichess games.
2. Engine-only: Stockfish best-move labels from a compatible licensed subset of ChessBench or a small independently annotated sample.
3. Mixed: a documented mixture of the above.

Keep evaluation fixed across arms. A single engine top move is not the only acceptable move; use a fixed engine protocol to measure move quality.

## Input/output

- Primary input: FEN only.
- Target: one UCI move.
- Recent history is out of scope for the first experiment.
- Validate outputs with python-chess; do not include legal-move lists in baseline prompt.

## Evaluation

- Legal move rate.
- Top-1 move agreement (secondary).
- Centipawn loss under fixed Stockfish version/configuration.
- Held-out puzzle performance.
- Games against fixed-strength opponents after first SFT model works.

Record data/model/tokenizer revisions, seeds, training settings, Stockfish configuration, opponent protocol and confidence intervals where practical.

## Improvement loop

After first SFT: categorise measurable errors; check for data-coverage issues; create targeted examples only for verified failure categories; compare second SFT against untouched baseline. Consider offline preference optimisation only if engine-ranked move pairs are available. Online RL is out of scope for the initial project.
