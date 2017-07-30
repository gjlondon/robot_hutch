from board import Board

__author__ = 'rogueleaderr'


def test_board_size():
    board = Board(board_height=3)
    assert len(board._board) == 3
    assert len(board._board[0]) == 3


def test_board_print():
    live_robots = [[True, False], [False, True]]
    board = Board(board_height=2, live_robots=live_robots)
    expected_board = "---------\n| * |   |\n---------\n|   | * |\n---------\n"
    assert str(board) == expected_board


def test_preconfiguring_board():
    live_robots = [[True, False], [False, True]]
    board = Board(board_height=2, live_robots=live_robots)
    assert board._board[0][0].alive
    assert not board._board[0][1].alive
    assert not board._board[1][0].alive
    assert board._board[1][1].alive
