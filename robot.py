import functools
import itertools
import json
import random
import threading

from mailbox import Mailbox

__author__ = 'rogueleaderr'


class Robot:
    def __init__(self, starts_alive, row_number, column_number, board_height, parthenogenesis):
        self.neighbor_mailbox_names = []
        self.column_number = column_number
        self.row_number = row_number
        self.alive = starts_alive
        self.parthenogenesis = parthenogenesis
        self.board_height = board_height
        self.enumerate_neighborhood_mailbox_addresses(board_height, column_number, row_number)

    @staticmethod
    def calculate_neighbor_addresses(board_height, column_number, row_number):
        # wrap edges of the _board to make a "toroidal" _board
        neighborhood_left_boundary = (column_number - 1) % board_height
        neighborhood_right_boundary = (column_number + 1) % board_height
        neighborhood_bottom_boundary = (row_number - 1) % board_height
        neighborhood_top_boundary = (row_number + 1) % board_height
        horizontal_boundaries = (neighborhood_left_boundary, column_number, neighborhood_right_boundary)
        vertical_boundaries = (neighborhood_bottom_boundary, row_number, neighborhood_top_boundary)
        neighbor_addresses = [(i, j) for i, j in itertools.product(vertical_boundaries, horizontal_boundaries)]
        return neighbor_addresses

    def enumerate_neighborhood_mailbox_addresses(self, board_height, column_number, row_number):
        neighbor_addresses = self.calculate_neighbor_addresses(board_height, column_number, row_number)
        for i, j in neighbor_addresses:
            address = "{}i-{}j".format(i, j)
            mailbox_name = "mailbox-{address}".format(address=address)
            if i == row_number and j == column_number:
                self.address = address
                self.incoming_mailbox_name = mailbox_name
            else:
                self.neighbor_mailbox_names.append(mailbox_name)
        assert len(self.neighbor_mailbox_names) == 8
        assert self.address not in self.neighbor_mailbox_names

    def __str__(self):
        status = "alive" if self.alive else "dead"
        return "Robot at {} is {}".format(self.address, status)

    def __repr__(self):
        return self.__str__()

    def start_running(self):
        incoming_mailbox_name = self.incoming_mailbox_name
        robot = self
        mailbox_initialized = threading.Event()
        allowed_to_start = threading.Event()
        fully_initialized = threading.Event()
        update_status = self.update_status
        board_height = self.board_height

        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls):
                mailbox = Mailbox(incoming_mailbox_name, update_status, board_height)
                robot.mailbox = mailbox
                mailbox_initialized.set()
                mailbox.report_mailbox_ready()
                # listen forever for ticks from the game clock
                mailbox.clock_channel.start_consuming()

        continuous_thread = ScheduleThread()
        # make sure the thread is cleaned up when the program is killed, e.g. by ctrl-C
        continuous_thread.setDaemon(True)
        continuous_thread.start()
        self.robot_thread = continuous_thread
        return mailbox_initialized, allowed_to_start, fully_initialized

    def stop_playing(self):
        try:
            self.mailbox.clock_channel.stop_consuming()
            self.robot_thread.join(10)
        except AttributeError:
            print("thread not yet available")

    def update_status(self, mailbox, ch, method, properties, body):
        message = json.loads(body)
        turn_number = message['turn_number']
        should_heartbeat = message['heartbeat']
        should_update_status = message['update_status']

        if should_update_status:
            living_neighbors = mailbox.check_for_mail()
            num_living_neighbors = len(living_neighbors)
            if self.alive:
                if num_living_neighbors < 2 or num_living_neighbors > 3:
                    self.alive = False
            else:
                if num_living_neighbors == 3:
                    self.alive = True
                else:
                    if self.parthenogenesis and random.random() > .995:
                        self.alive = True

        if should_heartbeat:
            self.broadcast_to_neighbors(mailbox)

        ch.basic_ack(method.delivery_tag)
        mailbox.acknowledge_batch()
        mailbox.tell_clock_turn_is_completed(turn_number)

    def broadcast_to_neighbors(self, mailbox: Mailbox):
        message = {"address": self.address,
                   "alive": self.alive}
        message_body = json.dumps(message)

        for neighbor_mailbox in self.neighbor_mailbox_names:
            mailbox.send_status_to_neighbors(neighbor_mailbox, message_body)
