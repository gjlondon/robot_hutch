import functools
import itertools
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

    def start_playing(self):
        incoming_mailbox_name = self.incoming_mailbox_name
        robot = self
        mailbox_initialized = threading.Event()
        allowed_to_start = threading.Event()
        fully_initialized = threading.Event()

        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls):
                mailbox = Mailbox(incoming_mailbox_name)
                robot.mailbox = mailbox
                mailbox_initialized.set()

                while not allowed_to_start.is_set():
                    # give other robots time to initialize their queues
                    pass

                # basic_consume won't let us pass arguments to the callback, so
                # make the callback a partial function that has the argument it needs
                update_status = functools.partial(self.update_status, mailbox)
                mailbox.clock_channel.basic_consume(update_status,
                                                    queue=mailbox.queue_from_clock)

                # send messages once at game start
                # so robots know who if their neigbbors are alive on the first turn
                if self.alive:
                    self.broadcast_to_neighbors(mailbox)
                fully_initialized.set()
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
        tick_count = body
        messages_from_neighbors = mailbox.check_for_mail()
        num_living_neighbors = len(messages_from_neighbors)
        if self.alive:
            if num_living_neighbors < 2 or num_living_neighbors > 3:
                self.alive = False
                # print('{} died on round {} because messages were: {}. Neighbors are {}'.format(self.address,
                #                                                                                tick_count,
                #                                                                                messages_from_neighbors,
                #                                                                                self.neighbor_mailbox_names))
        else:
            if num_living_neighbors == 3:
                self.alive = True
            else:
                if self.parthenogenesis and random.random() > .995:
                    self.alive = True

        if self.alive:
            self.broadcast_to_neighbors(mailbox)

        ch.basic_ack(method.delivery_tag)
        mailbox.acknowledge_batch()
        mailbox.tell_clock_turn_is_completed()

    def broadcast_to_neighbors(self, mailbox: Mailbox):
        message = self.address

        for neighbor_mailbox in self.neighbor_mailbox_names:
            mailbox.send_message_to_neighbor(neighbor_mailbox, message)
