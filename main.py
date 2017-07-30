#!/usr/bin/env python
import time

from board import Board
from clock import Clock, ExtinctionEvent

__author__ = 'rogueleaderr'

import sys


def main(argv):
    if argv is None:
        argv = sys.argv

    tick_length = 2
    board_height = 10
    board = Board(board_height=board_height, parthenogenesis=False)
    game_clock = Clock(board, tick_length=tick_length)
    # TODO message based initialization
    # TODO use topic queues instead of one queue per robot
    try:
        game_clock.start()
    except ExtinctionEvent:
        time.sleep(1)
        print("Everyone died")
        sys.exit(0)

if __name__ == "__main__":
    main(None)
