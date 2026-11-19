"""Collect a deterministic sample of Lichess PGN games and build FEN -> UCI SFT JSONL.

The source PGN is streamed from zstandard; the full uncompressed archive is never written to disk.
Human move labels are demonstrations, not engine-optimal labels.
"""
import argparse
import collections
import gzip
import hashlib
import io
import json
import random
from pathlib import Path

import chess
import chess.pgn
import zstandard


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def game_identifier(game: chess.pgn.Game) -> str:
    for key in ("GameId", "Site"):
        value = game.headers.get(key)
        if value and value != "?":
            return value.rstrip("/").split("/")[-1]
    return hashlib.sha256(str(game).encode("utf-8")).hexdigest()[:24]


def base_time_seconds(value: str) -> int | None:
    if not value or value == "?":
        return None
    base = value.split("+", 1)[0]
    if "/" in base or ":" in base:
        return None
    try:
        return int(base)
    except ValueError:
        return None


def eligible_game(game: chess.pgn.Game, min_elo: int, min_base_seconds: int) -> bool:
    headers = game.headers
    if headers.get("Variant", "Standard").lower() not in ("standard", "chess"):
        return False
    if headers.get("WhiteTitle", "").upper() == "BOT" or headers.get("BlackTitle", "").upper() == "BOT":
        return False
    if headers.get("Result") not in ("1-0", "0-1", "1/2-1/2"):
        return False
    try:
        if min(int(headers.get("WhiteElo", "")), int(headers.get("BlackElo", ""))) < min_elo:
            return False
    except (TypeError, ValueError):
        return False
    seconds = base_time_seconds(headers.get("TimeControl", ""))
    return seconds is not None and seconds >= min_base_seconds


def stable_split(game_id: str) -> str:
    bucket = int(hashlib.sha256(game_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    if bucket < 90:
        return "train"
    if bucket < 95:
        return "validation"
    return "test"


def read_reservoir(pgn_zst: Path, limit: int, min_elo: int, min_base_seconds: int, seed: int):
    rng = random.Random(seed)
    reservoir = []
    eligible_count = 0
    games_read = 0
    with pgn_zst.open("rb") as raw:
        reader = zstandard.ZstdDecompressor().stream_reader(raw)
        text_stream = io.TextIOWrapper(reader, encoding="utf-8", errors="replace")
        while True:
            game = chess.pgn.read_game(text_stream)
            if game is None:
                break
            games_read += 1
            if not eligible_game(game, min_elo, min_base_seconds):
                continue
            eligible_count += 1
            item = (game_identifier(game), str(game))
            if len(reservoir) < limit:
                reservoir.append(item)
            else:
                index = rng.randrange(eligible_count)
                if index < limit:
                    reservoir[index] = item
        text_stream.close()
    return reservoir, games_read, eligible_count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pgn-zst", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-games", type=int, default=1000, help="Reservoir sample size after filtering")
    parser.add_argument("--min-elo", type=int, default=1800)
    parser.add_argument("--min-base-seconds", type=int, default=180, help="Exclude bullet/ultrabullet")
    parser.add_argument("--max-plies-per-game", type=int, default=120)
    parser.add_argument("--seed", type=int, default=20261119)
    parser.add_argument("--source-url", default="https://database.lichess.org/standard/lichess_db_standard_rated_2014-01.pgn.zst")
    args = parser.parse_args()

    source_path = Path(args.pgn_zst)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    sampled, games_read, eligible_count = read_reservoir(
        source_path, args.max_games, args.min_elo, args.min_base_seconds, args.seed
    )
    if not sampled:
        raise SystemExit("No games passed the filters. Check the archive and/or relax filters.")

    # First assign whole games to splits. Aggregate repeated exact FENs within each split.
    by_split = {name: {} for name in ("train", "validation", "test")}
    fen_splits = collections.defaultdict(set)
    game_splits = collections.Counter()
    invalid_positions = 0
    invalid_moves = 0
    sampled.sort(key=lambda item: item[0])

    for game_id, game_text in sampled:
        game = chess.pgn.read_game(io.StringIO(game_text))
        if game is None:
            continue
        split = stable_split(game_id)
        game_splits[split] += 1
        board = game.board()
        for ply, move in enumerate(game.mainline_moves()):
            if ply >= args.max_plies_per_game:
                break
            if not board.is_valid():
                invalid_positions += 1
                break
            if move not in board.legal_moves:
                invalid_moves += 1
                break
            fen = board.fen()
            fen_splits[fen].add(split)
            entry = by_split[split].setdefault(
                fen, {"moves": collections.Counter(), "games": set(), "ply_min": ply, "ply_max": ply}
            )
            entry["moves"][move.uci()] += 1
            entry["games"].add(game_id)
            entry["ply_min"] = min(entry["ply_min"], ply)
            entry["ply_max"] = max(entry["ply_max"], ply)
            board.push(move)

    # Remove any exact FEN that appears in more than one game-level split.
    cross_split_fens = {fen for fen, splits in fen_splits.items() if len(splits) > 1}
    records_by_split = collections.Counter()
    rows = []
    for split, positions in by_split.items():
        for fen, entry in positions.items():
            if fen in cross_split_fens:
                continue
            total = sum(entry["moves"].values())
            # Majority human move; lexical tie-break makes output deterministic.
            target, target_count = sorted(entry["moves"].items(), key=lambda pair: (-pair[1], pair[0]))[0]
            board = chess.Board(fen)
            move = chess.Move.from_uci(target)
            if not board.is_valid() or move not in board.legal_moves:
                invalid_positions += 1
                continue
            sample_id = hashlib.sha256(f"{split}|{fen}".encode("utf-8")).hexdigest()[:20]
            prompt = (
                "Given this chess position in FEN, choose one legal move. "
                "Reply with exactly one UCI move and no explanation.\nFEN: " + fen
            )
            rows.append({
                "sample_id": sample_id,
                "source": "human_lichess",
                "fen": fen,
                "target_move_uci": target,
                "split": split,
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": target},
                ],
                "metadata": {
                    "observations": total,
                    "target_move_observations": target_count,
                    "target_agreement": round(target_count / total, 4),
                    "source_game_count": len(entry["games"]),
                    "min_ply": entry["ply_min"],
                    "max_ply": entry["ply_max"],
                    "label_type": "human_move",
                },
            })
            records_by_split[split] += 1

    rows.sort(key=lambda row: (row["split"], row["sample_id"]))
    if not rows:
        raise SystemExit("No SFT records survived validation and split de-duplication.")

    # Deterministic gzip output.
    with out_path.open("wb") as raw_out:
        with gzip.GzipFile(fileobj=raw_out, mode="wb", mtime=0, compresslevel=6) as gz:
            with io.TextIOWrapper(gz, encoding="utf-8") as text_out:
                for row in rows:
                    text_out.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    summary = {
        "source_url": args.source_url,
        "source_archive": source_path.name,
        "source_archive_sha256": sha256_file(source_path),
        "seed": args.seed,
        "games_read": games_read,
        "eligible_games_seen": eligible_count,
        "games_sampled": len(sampled),
        "games_sampled_by_split": dict(game_splits),
        "records_by_split": dict(records_by_split),
        "total_sft_records": len(rows),
        "cross_split_fen_collisions_removed": len(cross_split_fens),
        "invalid_positions_or_boards": invalid_positions,
        "illegal_moves_encountered": invalid_moves,
        "filters": {
            "variant": "standard",
            "both_player_ratings_at_least": args.min_elo,
            "minimum_base_time_control_seconds": args.min_base_seconds,
            "exclude_bots": True,
            "completed_games_only": True,
            "max_plies_per_game": args.max_plies_per_game,
        },
        "split_method": "stable SHA-256 hash of original game identifier; exact FENs occurring across splits removed from all splits",
        "label_method": "majority human move for repeated exact FENs within a split; ties broken lexically",
        "note": "Pilot dataset only. Human moves are not necessarily engine-optimal.",
    }
    summary_path = out_path.with_suffix(out_path.suffix + ".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    manifest = {
        "dataset_name": "lichess-standard-human-moves-pilot",
        "format": "gzip-compressed JSON Lines",
        "data_file": out_path.name,
        "data_file_sha256": sha256_file(out_path),
        "source_archive_sha256": summary["source_archive_sha256"],
        "source_url": args.source_url,
        "source_license": "CC0-1.0 (Lichess database export)",
        "retrieval_date_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "model_target": "google/gemma-3-270m-it",
        "input": "FEN only",
        "target": "one UCI move",
        "summary_file": summary_path.name,
        "limitations": [
            "Human moves are behavioural demonstrations, not guaranteed best moves.",
            "Pilot uses a single historical monthly archive and is not a final representative corpus.",
            "FEN does not encode the complete repetition history of a game.",
        ],
    }
    manifest_path = out_path.parent / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Dataset: {out_path} ({out_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
