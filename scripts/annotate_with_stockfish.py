"""Optional CPU-side Stockfish annotation utility; intentionally not run automatically."""
import argparse
import json
from pathlib import Path

import chess
import chess.engine


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSONL records containing at least a fen field")
    parser.add_argument("--out", required=True)
    parser.add_argument("--stockfish", required=True, help="Path to Stockfish executable")
    parser.add_argument("--depth", type=int, default=12)
    args = parser.parse_args()

    engine = chess.engine.SimpleEngine.popen_uci(args.stockfish)
    try:
        with Path(args.input).open(encoding="utf-8") as src, Path(args.out).open("w", encoding="utf-8") as dst:
            for line in src:
                row = json.loads(line)
                board = chess.Board(row["fen"])
                info = engine.analyse(board, chess.engine.Limit(depth=args.depth))
                best = info["pv"][0]
                row["target_move_uci"] = best.uci()
                row["engine_eval_cp"] = info["score"].pov(board.turn).score(mate_score=100000)
                row["engine_depth"] = info.get("depth", args.depth)
                row["source"] = "stockfish_generated"
                row["teacher_engine"] = "Stockfish; record exact version separately"
                dst.write(json.dumps(row, ensure_ascii=False) + "\n")
    finally:
        engine.quit()


if __name__ == "__main__":
    main()
