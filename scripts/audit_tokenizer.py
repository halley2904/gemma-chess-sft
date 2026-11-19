import argparse
import json
from pathlib import Path
from transformers import AutoTokenizer

POSITIONS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
    "8/5pk1/6p1/8/8/6P1/5PK1/8 w - - 0 1",
]
MOVES = ["e2e4", "g1f3", "e7e8q", "e1g1"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="google/gemma-3-270m-it")
    parser.add_argument("--out", default="results/tokenizer_audit.json")
    args = parser.parse_args()
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    report = {"model": args.model, "positions": [], "moves": [],
              "note": "Token counts are diagnostic; fragmentation alone does not prove unsuitability."}
    for fen in POSITIONS:
        ids = tokenizer(fen, add_special_tokens=False)["input_ids"]
        report["positions"].append({"fen": fen, "token_count": len(ids), "tokens": tokenizer.convert_ids_to_tokens(ids)})
    for move in MOVES:
        ids = tokenizer(move, add_special_tokens=False)["input_ids"]
        report["moves"].append({"uci": move, "token_count": len(ids), "tokens": tokenizer.convert_ids_to_tokens(ids)})
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
