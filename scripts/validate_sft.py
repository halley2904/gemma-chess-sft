import argparse
import gzip
import json
from pathlib import Path

import chess


def open_jsonl(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    totals = {
        "records": 0, "valid_fen": 0, "legal_target": 0,
        "bad_json": 0, "bad_fen": 0, "illegal_target": 0,
        "records_by_split": {},
    }
    seen_ids = set()
    with open_jsonl(Path(args.input)) as stream:
        for line in stream:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                totals["bad_json"] += 1
                continue
            totals["records"] += 1
            if row.get("sample_id") in seen_ids:
                raise SystemExit(f"Duplicate sample_id: {row.get('sample_id')}")
            seen_ids.add(row.get("sample_id"))
            split = row.get("split", "missing")
            totals["records_by_split"][split] = totals["records_by_split"].get(split, 0) + 1
            try:
                board = chess.Board(row["fen"])
                if not board.is_valid():
                    raise ValueError("invalid board")
                totals["valid_fen"] += 1
            except Exception:
                totals["bad_fen"] += 1
                continue
            try:
                move = chess.Move.from_uci(row["target_move_uci"])
                if move not in board.legal_moves:
                    raise ValueError("illegal move")
                totals["legal_target"] += 1
            except Exception:
                totals["illegal_target"] += 1
    print(json.dumps(totals, indent=2))
    if totals["bad_json"] or totals["bad_fen"] or totals["illegal_target"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
