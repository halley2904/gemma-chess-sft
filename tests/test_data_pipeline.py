import json
from pathlib import Path

import chess

from scripts.collect_lichess_sft import base_time_seconds, stable_split


def test_illustrative_record_is_valid_and_legal():
    path = Path("data/examples/illustrative_only.jsonl")
    row = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    board = chess.Board(row["fen"])
    move = chess.Move.from_uci(row["target_move_uci"])
    assert board.is_valid()
    assert move in board.legal_moves
    assert row["split"] == "illustrative"


def test_time_control_filter_parses_base_seconds():
    assert base_time_seconds("300+0") == 300
    assert base_time_seconds("180+2") == 180
    assert base_time_seconds("60+0") == 60
    assert base_time_seconds("?") is None
    assert base_time_seconds("40/7200:3600") is None


def test_game_split_is_deterministic_and_valid():
    assert stable_split("lichess-game-123") == stable_split("lichess-game-123")
    assert stable_split("lichess-game-123") in {"train", "validation", "test"}
