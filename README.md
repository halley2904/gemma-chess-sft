# Gemma Chess SFT

A lightweight, reproducible chess move-learning project using **one pretrained model: Gemma 3 270M IT**.

## Fixed scope

- Model: `google/gemma-3-270m-it` only.
- Task: given a chess position as FEN, predict one move in UCI format.
- Training method: supervised fine-tuning (SFT).
- Chess rules and move validation: `python-chess`.
- Data: human Lichess standard-rated games first; engine-labelled data is a separate later experiment.
- Compute plan: Kaggle free GPU for training. GitHub Actions is used only for small CPU-side data preparation.
- No second model, no model-from-scratch work, and no online RL in the initial project.

## Data workflow

1. Sample a documented subset of Lichess standard-rated games.
2. Filter standard games, completed results, player ratings and time controls.
3. Extract each board position and the human move played from it.
4. Validate FENs and legal target moves with python-chess.
5. Split by original game, deduplicate exact positions and remove cross-split position collisions.
6. Write compressed SFT JSONL plus a manifest and quality summary.

The first automated pilot uses the complete January 2013 Lichess standard-game archive (about 17.8 MB compressed, 121,332 games). It samples up to 1,000 eligible games deterministically. This is a small pipeline pilot, not the final training corpus.

## SFT format

Each record contains a FEN-only user prompt and one UCI move as the assistant target. Human moves are demonstrations of human play, not claims of engine-optimal play. The dataset includes source, split and label-agreement metadata.

## Run locally

```bash
pip install -e ".[dev]"
python scripts/collect_lichess_sft.py --pgn-zst path/to/lichess.pgn.zst --out data/processed/pilot.jsonl.gz
python scripts/validate_sft.py --input data/processed/pilot.jsonl.gz
python scripts/audit_tokenizer.py --model google/gemma-3-270m-it
```

Accept Google's Gemma terms on Hugging Face before downloading the model/tokenizer.

## GitHub Actions

The workflow `.github/workflows/collect-data.yml` downloads the documented pilot archive, creates and validates the compressed SFT dataset, and commits the resulting small pilot plus manifest/summary to this repository. Check the Actions tab for its run and logs.

Large raw archives, model weights and training checkpoints are never committed to Git. The pilot dataset is compressed and size-checked before upload.

## Sources and licences

- Lichess database: https://database.lichess.org/
- Lichess database tooling: https://github.com/lichess-org/database
- Gemma 3 270M IT: https://huggingface.co/google/gemma-3-270m-it
- Searchless Chess / ChessBench reference: https://arxiv.org/abs/2402.04494

Lichess database exports are released under CC0. Gemma weights are subject to Google's Gemma Terms of Use. Always inspect the exact licence of any additional source before redistributing it.

## Evaluation

Primary metrics: legal move rate and centipawn loss under a fixed Stockfish protocol. Secondary metrics: top-1 move agreement, puzzle performance, playing results against fixed-strength opponents, latency and memory. Elo is only meaningful with a documented opponent and match protocol.

## Status

- [x] Project scaffold and data schema
- [x] Deterministic Lichess pilot collection pipeline
- [x] GitHub Actions and quality checks
- [ ] Collect and inspect pilot dataset
- [ ] Freeze a larger train/validation/test corpus
- [ ] Training (not started)
