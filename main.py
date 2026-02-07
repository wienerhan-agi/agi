#!/usr/bin/env python3
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

BOARD_ROWS = 10
BOARD_COLS = 9

FILES = "abcdefghi"

RED = "red"
BLACK = "black"


@dataclass(frozen=True)
class Move:
    src: Tuple[int, int]
    dst: Tuple[int, int]


PIECE_NAMES = {
    "K": "帥",
    "A": "仕",
    "B": "相",
    "N": "傌",
    "R": "俥",
    "C": "炮",
    "P": "兵",
    "k": "將",
    "a": "士",
    "b": "象",
    "n": "馬",
    "r": "車",
    "c": "砲",
    "p": "卒",
    ".": "·",
}


def initial_board() -> list[list[str]]:
    board = [["." for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
    # Black pieces (top)
    board[0] = list("rnbakabnr")
    board[2][1] = "c"
    board[2][7] = "c"
    board[3][0] = "p"
    board[3][2] = "p"
    board[3][4] = "p"
    board[3][6] = "p"
    board[3][8] = "p"
    # Red pieces (bottom)
    board[9] = list("RNBAKABNR")
    board[7][1] = "C"
    board[7][7] = "C"
    board[6][0] = "P"
    board[6][2] = "P"
    board[6][4] = "P"
    board[6][6] = "P"
    board[6][8] = "P"
    return board


def print_board(board: list[list[str]]) -> None:
    print("    " + " ".join(FILES))
    for row in range(BOARD_ROWS):
        rank = BOARD_ROWS - row
        line = [PIECE_NAMES[p] for p in board[row]]
        print(f" {rank:2d} " + " ".join(line))
    print("    " + " ".join(FILES))


def parse_coord(token: str) -> Optional[Tuple[int, int]]:
    token = token.strip().lower()
    if len(token) < 2 or len(token) > 3:
        return None
    file_char = token[0]
    if file_char not in FILES:
        return None
    try:
        rank = int(token[1:])
    except ValueError:
        return None
    if not 1 <= rank <= 10:
        return None
    col = FILES.index(file_char)
    row = BOARD_ROWS - rank
    return row, col


def parse_move(text: str) -> Optional[Move]:
    text = text.replace("-", " ").replace(",", " ").strip()
    if len(text) == 4 and text[0] in FILES and text[2] in FILES:
        src = parse_coord(text[:2])
        dst = parse_coord(text[2:])
    else:
        parts = [p for p in text.split() if p]
        if len(parts) != 2:
            return None
        src = parse_coord(parts[0])
        dst = parse_coord(parts[1])
    if src is None or dst is None:
        return None
    return Move(src, dst)


def in_bounds(row: int, col: int) -> bool:
    return 0 <= row < BOARD_ROWS and 0 <= col < BOARD_COLS


def piece_color(piece: str) -> Optional[str]:
    if piece == ".":
        return None
    return RED if piece.isupper() else BLACK


def same_color(piece: str, color: str) -> bool:
    return piece_color(piece) == color


def opponent(color: str) -> str:
    return BLACK if color == RED else RED


def is_palace(row: int, col: int, color: str) -> bool:
    if color == RED:
        return 7 <= row <= 9 and 3 <= col <= 5
    return 0 <= row <= 2 and 3 <= col <= 5


def on_own_side(row: int, color: str) -> bool:
    if color == RED:
        return row >= 5
    return row <= 4


def river_crossed(row: int, color: str) -> bool:
    if color == RED:
        return row <= 4
    return row >= 5


def clear_path(board: list[list[str]], src: Tuple[int, int], dst: Tuple[int, int]) -> bool:
    sr, sc = src
    dr, dc = dst
    if sr == dr:
        step = 1 if dc > sc else -1
        for c in range(sc + step, dc, step):
            if board[sr][c] != ".":
                return False
        return True
    if sc == dc:
        step = 1 if dr > sr else -1
        for r in range(sr + step, dr, step):
            if board[r][sc] != ".":
                return False
        return True
    return False


def count_screens(board: list[list[str]], src: Tuple[int, int], dst: Tuple[int, int]) -> int:
    sr, sc = src
    dr, dc = dst
    screens = 0
    if sr == dr:
        step = 1 if dc > sc else -1
        for c in range(sc + step, dc, step):
            if board[sr][c] != ".":
                screens += 1
    elif sc == dc:
        step = 1 if dr > sr else -1
        for r in range(sr + step, dr, step):
            if board[r][sc] != ".":
                screens += 1
    return screens


def find_king(board: list[list[str]], color: str) -> Tuple[int, int]:
    target = "K" if color == RED else "k"
    for r in range(BOARD_ROWS):
        for c in range(BOARD_COLS):
            if board[r][c] == target:
                return r, c
    raise ValueError("King not found")


def is_flying_general(board: list[list[str]]) -> bool:
    red_king = find_king(board, RED)
    black_king = find_king(board, BLACK)
    if red_king[1] != black_king[1]:
        return False
    return clear_path(board, red_king, black_king)


def legal_move_for_piece(
    board: list[list[str]],
    src: Tuple[int, int],
    dst: Tuple[int, int],
    color: str,
) -> bool:
    sr, sc = src
    dr, dc = dst
    piece = board[sr][sc]
    target = board[dr][dc]
    if piece == "." or not same_color(piece, color):
        return False
    if target != "." and same_color(target, color):
        return False
    pr, pc = dr - sr, dc - sc
    piece_type = piece.upper()

    if piece_type == "R":
        return (sr == dr or sc == dc) and clear_path(board, src, dst)

    if piece_type == "C":
        if sr != dr and sc != dc:
            return False
        screens = count_screens(board, src, dst)
        if target == ".":
            return screens == 0
        return screens == 1

    if piece_type == "N":
        if (abs(pr), abs(pc)) not in {(2, 1), (1, 2)}:
            return False
        if abs(pr) == 2:
            leg = (sr + pr // 2, sc)
        else:
            leg = (sr, sc + pc // 2)
        return board[leg[0]][leg[1]] == "."

    if piece_type == "B":
        if (abs(pr), abs(pc)) != (2, 2):
            return False
        if not on_own_side(dr, color):
            return False
        eye = (sr + pr // 2, sc + pc // 2)
        return board[eye[0]][eye[1]] == "."

    if piece_type == "A":
        if (abs(pr), abs(pc)) != (1, 1):
            return False
        return is_palace(dr, dc, color)

    if piece_type == "K":
        if (abs(pr), abs(pc)) not in {(1, 0), (0, 1)}:
            return False
        return is_palace(dr, dc, color)

    if piece_type == "P":
        forward = -1 if color == RED else 1
        if pr == forward and pc == 0:
            return True
        if river_crossed(sr, color) and pr == 0 and abs(pc) == 1:
            return True
        return False

    return False


def is_in_check(board: list[list[str]], color: str) -> bool:
    king_pos = find_king(board, color)
    enemy = opponent(color)
    for r in range(BOARD_ROWS):
        for c in range(BOARD_COLS):
            piece = board[r][c]
            if piece == "." or piece_color(piece) != enemy:
                continue
            if legal_move_for_piece(board, (r, c), king_pos, enemy):
                return True
    if is_flying_general(board):
        return True
    return False


def make_move(board: list[list[str]], move: Move) -> list[list[str]]:
    new_board = [row[:] for row in board]
    sr, sc = move.src
    dr, dc = move.dst
    new_board[dr][dc] = new_board[sr][sc]
    new_board[sr][sc] = "."
    return new_board


def legal_move(board: list[list[str]], move: Move, color: str) -> bool:
    if not in_bounds(*move.src) or not in_bounds(*move.dst):
        return False
    if not legal_move_for_piece(board, move.src, move.dst, color):
        return False
    next_board = make_move(board, move)
    if is_flying_general(next_board):
        return False
    if is_in_check(next_board, color):
        return False
    return True


def all_legal_moves(board: list[list[str]], color: str) -> Iterable[Move]:
    for r in range(BOARD_ROWS):
        for c in range(BOARD_COLS):
            if piece_color(board[r][c]) != color:
                continue
            for dr in range(BOARD_ROWS):
                for dc in range(BOARD_COLS):
                    move = Move((r, c), (dr, dc))
                    if legal_move(board, move, color):
                        yield move


def game_status(board: list[list[str]], color: str) -> str:
    enemy = opponent(color)
    if is_in_check(board, enemy):
        if not any(all_legal_moves(board, enemy)):
            return f"{color} wins by checkmate!"
        return f"{enemy} is in check."
    if not any(all_legal_moves(board, enemy)):
        return f"Stalemate. {color} wins."
    return ""


def prompt(color: str) -> str:
    label = "红" if color == RED else "黑"
    return f"{label}方走棋 (如 a1 a2, help, quit): "


def main() -> int:
    board = initial_board()
    turn = RED
    print("中国象棋 - 终端版")
    print_board(board)

    while True:
        status = game_status(board, opponent(turn))
        if status:
            print(status)
        if "wins" in status:
            break

        user_input = input(prompt(turn)).strip()
        if user_input.lower() in {"quit", "exit"}:
            print("已退出。")
            return 0
        if user_input.lower() in {"help", "?"}:
            print("输入格式: a1 a2 或 a1a2，列为 a-i，行为 1-10 (红方在下)。")
            continue

        move = parse_move(user_input)
        if move is None:
            print("无法解析输入，请重试。")
            continue
        if not legal_move(board, move, turn):
            print("非法走法，请重试。")
            continue
        board = make_move(board, move)
        print_board(board)
        turn = opponent(turn)
    return 0


if __name__ == "__main__":
    sys.exit(main())
