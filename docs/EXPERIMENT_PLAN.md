# Experiment plan (training intentionally pending)

## Single-model scope

Use only `google/gemma-3-270m-it`. Do not add Qwen or a from-scratch baseline.

## Data arms

1. Human-only: moves from higher-rated Lichess games.
2. Engine-only: Stockfish best-move labels from a compatible licensed subset of ChessBench or a small independently annotated sample.
3. Mixed: a documented mixture of the above.

Keep evaluation fixed across arms. A single engine top move is not the only acceptable move; use a fixed engine protocol to measure move quality.

## Input/output

- Primary input: FEN only.
- Target: one UCI move.
- Recent history is out of scope for the first experiment.
- Do not include legal-move lists in the baseline prompt; validate predictions with python-chess.

## Evaluation

- Legal move rate.
- Top-1 move agreement (secondary).
- Centipawn loss under fixed Stockfish version/configuration.
- Held-out puzzle performance.
- Games against fixed-strength opponents after the first SFT model works.

Record data/model/tokenizer revisions, seeds, training settings, Stockfish version/settings, opponent protocol, and confidence intervals where practical.

## Improvement loop

After first SFT:
1. Categorise measurable errors (illegal move, missed forced tactic, obvious hanging piece, etc.).
2. Check whether errors reflect coverage or model behaviour.
3. Create targeted examples only for verified failure categories.
4. Compare second SFT against the untouched baseline.
5. Consider offline preference optimisation only if engine-ranked move pairs are available and useful.

Online RL is out of scope for the initial project.
