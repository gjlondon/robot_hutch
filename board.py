import random
from robot import Robot

__author__ = 'rogueleaderr'


class Board:
    def __init__(self, board_height=8, live_robots=None, parthenogenesis=False):
        self.board_height = board_height
        _board = []
        for i in range(board_height):
            row = []
            for j in range(board_height):
                if not live_robots:
                    robot_starts_alive = random.choice([True, False])
                else:
                    robot_starts_alive = live_robots[i][j]
                robot = Robot(robot_starts_alive, i, j, board_height, parthenogenesis)
                row.append(robot)
            _board.append(row)
        self._board = _board

    def __str__(self):
        boolean_board = [[robot.alive for robot in row] for row in self._board]
        return self.print_boolean_board(boolean_board)

    @staticmethod
    def print_boolean_board(_board):
        board_height = len(_board)
        output = ""
        horizontal_line = "-" + "----" * board_height + "\n"
        for row in _board:
            output += horizontal_line
            row_representation = "|"
            for alive in row:
                marker = "*" if alive else " "
                box = " {} ".format(marker)
                row_representation += box
                row_representation += "|"
            output += row_representation + "\n"
        output += horizontal_line
        return output

    def start_robots(self):
        print("waking up robots.")
        mailboxes_initialized = []
        start_permits = []
        robots_initialized = []
        for row in self._board:
            for robot in row:
                initialized, allowed_to_start, fully_initialized = robot.start_playing()
                mailboxes_initialized.append(initialized)
                start_permits.append(allowed_to_start)
                robots_initialized.append(fully_initialized)
                print(".", end='')
        print("")
        # wait for all the queues to be set up before proceeding
        # can't send messages to queues that don't exist yet or they'll be lost
        while not all([event.is_set() for event in mailboxes_initialized]):
            pass
        print("mailboxes initialized")
        for permit in start_permits:
            permit.set()
        while not all([event.is_set() for event in robots_initialized]):
            # give them time to send their first messages
            pass
        print("robots activated")

    @property
    def extinct(self):
        living_cells = 0
        for row in self._board:
            for robot in row:
                living_cells += robot.alive
        return not living_cells
