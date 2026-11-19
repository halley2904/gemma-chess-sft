# Gemma Chess SFT

A lightweight, reproducible chess-learning research project inspired by an iterative SFT/evaluation/recovery workflow for small-model game playing.

## Fixed scope

- **One model only:** `google/gemma-3-270m-it` (Gemma 3 270M instruction-tuned).
- No Qwen, no second model, and no from-scratch model.
- No online RL in the initial study; consider further optimisation only after SFT evaluation.
- Compute: Kaggle free notebooks. Design runs to resume after interruption.
- Input: FEN only in the primary experiment.
- Output: one UCI move, e.g. `e2e4`.
- Validate moves with `python-chess`; model outputs are not assumed legal.

## Research question

How effectively can a small pretrained language model, Gemma 3 270M, learn chess move selection through supervised fine-tuning, and which source of move supervision is most useful?

This project does not claim that a general-purpose 270M language model will match a chess engine or reproduce Searchless Chess results.

## Workflow

1. Audit Gemma tokenizer on FEN and UCI strings.
2. Download a small, documented subset of licensed chess data.
3. Parse games/positions and validate FEN and target moves.
4. Split by original game before extracting positions; deduplicate exact FENs across splits.
5. Build SFT JSONL records.
6. Run baseline evaluation and SFT on Kaggle.
7. Analyse failures and create targeted examples only when justified by evidence.
8. Re-evaluate and publish code, data manifests, model card and demo.

## Data sources

### Lichess

- Database: https://database.lichess.org/
- Tooling: https://github.com/lichess-org/database
- Monthly standard-rated PGN exports; use a manageable sample.
- Lichess states its database exports are CC0. Verify terms for the exact selected artifact before redistribution.

### ChessBench / Searchless Chess

- Paper: https://arxiv.org/abs/2402.04494
- Code/data instructions: https://github.com/google-deepmind/searchless_chess
- ChessBench is a useful research reference and possible engine-label source.
- **Licensing:** repository components have different terms (including CC0 and CC-BY for data, CC-BY for weights, Apache-2.0 for software). Check the exact artifact's terms before using or redistributing it. Do not assume the entire corpus is CC0.
- The full action-value corpus is very large; do not download it for this project.

### Gemma

- Model: https://huggingface.co/google/gemma-3-270m-it
- Gemma is open-weight but subject to Google's Gemma Terms of Use. Accept the model conditions before downloading.
- Do not upload model weights to this repository.

## Data policy

Git stores preprocessing code, schema, prompt template, source manifests, small illustrative examples, checksums and split manifests. It does not store large PGN archives, full ChessBench shards, model weights or large generated datasets. Store large datasets in versioned Kaggle Datasets or Hugging Face Datasets and record exact versions, source URLs, licences, filters and SHA-256 checksums here.

## SFT record format

Each JSONL record includes `sample_id`, `source`, optional `game_id`, `fen`, `target_move_uci`, optional engine evaluation/depth, `split`, and chat-style `messages`. See `data/schema/sft.schema.json` and `data/examples/illustrative_only.jsonl`.

The baseline prompt exposes FEN only. Legal-move lists are reserved for a future constrained-decoding ablation so legality remains measurable.

## Evaluation

Primary metrics: legal move rate and centipawn loss under a fixed Stockfish protocol. Secondary metrics: top-1 move agreement, held-out puzzle performance, games against fixed-strength opponents, inference latency and memory use. Record engine version/settings, opponent settings, colour, game count and illegal-move policy. Do not compare Elo scores from different platforms/protocols as interchangeable.

## First setup

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
python scripts/audit_tokenizer.py --model google/gemma-3-270m-it
```

Accept Google's Gemma terms on Hugging Face and authenticate where required.

## Small human-game pilot

Put a small Lichess PGN sample at `data/raw/lichess/sample.pgn`, then run:

```bash
python scripts/build_human_sft.py --pgn data/raw/lichess/sample.pgn --out data/processed/human_pilot.jsonl --max-games 1000 --min-elo 1800
python scripts/validate_sft.py --input data/processed/human_pilot.jsonl
```

The pilot is a pipeline smoke test, not a claim of sufficient training scale.

## Kaggle

See `kaggle/README.md` and `kaggle/notebooks/00_environment_audit.py`. Actual accelerator and quota must be checked in your account. Save checkpoints in `/kaggle/working` and export them as versioned Kaggle Dataset/notebook outputs.

## Status

- [x] Initial scope and schema documented
- [x] Starter data-preparation, validation and tokenizer-audit scripts added
- [ ] Verify Kaggle account quota and accelerator
- [ ] Accept Gemma terms and run tokenizer audit
- [ ] Download and validate a small pilot PGN
- [ ] Generate and inspect pilot SFT records
- [ ] Freeze train/validation/test manifests
- [ ] Training (intentionally not started)

## Citation

Cite the exact Lichess exports, Searchless Chess/ChessBench resources, Gemma model revision and all preprocessing choices used in the final experiment.
