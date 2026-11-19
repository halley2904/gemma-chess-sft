import argparse
import hashlib
import json
from pathlib import Path

import chess
import chess.pgn
from tqdm import tqdm


def stable_split(game_id: str) -> str:
    value = int(hashlib.sha256(game_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    return "train" if value < 90 else ("validation" if value < 95 else "test")


def make_messages(fen: str, move_uci: str):
    return [
        {
            "role": "user",
            "content": (
                "Given this chess position in FEN, choose one legal move. "
                "Reply with exactly one UCI move and no explanation.\nFEN: " + fen
            ),
        },
        {"role": "assistant", "content": move_uci},
    ]


def main():
    parser = argparse.ArgumentParser(description="Convert PGN sample into validated FEN -> UCI SFT records.")
    parser.add_argument("--pgn", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-games", type=int, default=1000)
    parser.add_argument("--min-elo", type=int, default=1800)
    parser.add_argument("--max-plies-per-game", type=int, default=120)
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    seen_fens = set()
    counts = {"train": 0, "validation": 0, "test": 0}
    skipped = {"rating": 0, "invalid": 0, "duplicate_fen": 0}
    game_count = 0

    with Path(args.pgn).open("r", encoding="utf-8", errors="replace") as src, out_path.open("w", encoding="utf-8") as dst:
        pbar = tqdm(total=args.max_games, desc="Games")
        while game_count < args.max_games:
            game = chess.pgn.read_game(src)
            if game is None:
                break
            game_count += 1
            pbar.update(1)

            try:
                if min(int(game.headers.get("WhiteElo", "")), int(game.headers.get("BlackElo", ""))) < args.min_elo:
                    skipped["rating"] += 1
                    continue
            except (ValueError, TypeError):
                skipped["rating"] += 1
                continue

            if game.headers.get("Variant", "Standard") not in ("Standard", "Chess"):
                continue

            game_id = game.headers.get("GameId") or game.headers.get("Site") or f"game-{game_count}"
            split = stable_split(game_id)
            board = game.board()

            for ply, move in enumerate(game.mainline_moves()):
                if ply >= args.max_plies_per_game:
                    break
                fen = board.fen()
                if not board.is_valid() or move not in board.legal_moves:
                    skipped["invalid"] += 1
                    break
                fen_key = hashlib.sha256(fen.encode("utf-8")).hexdigest()
                if fen_key in seen_fens:
                    skipped["duplicate_fen"] += 1
                    board.push(move)
                    continue
                seen_fens.add(fen_key)
                row = {
                    "sample_id": f"{game_id}:{ply}",
                    "source": "human_lichess",
                    "game_id": game_id,
                    "fen": fen,
                    "target_move_uci": move.uci(),
                    "engine_eval_cp": None,
                    "engine_depth": None,
                    "split": split,
                    "messages": make_messages(fen, move.uci()),
                    "metadata": {
                        "white_elo": int(game.headers["WhiteElo"]),
                        "black_elo": int(game.headers["BlackElo"]),
                        "result": game.headers.get("Result"),
                        "ply": ply,
                        "time_control": game.headers.get("TimeControl"),
                    },
                }
                dst.write(json.dumps(row, ensure_ascii=False) + "\n")
                counts[split] += 1
                board.push(move)
        pbar.close()

    summary = {
        "games_read": game_count,
        "records_by_split": counts,
        "skipped": skipped,
        "source_file": args.pgn,
    }
    out_path.with_suffix(".summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
