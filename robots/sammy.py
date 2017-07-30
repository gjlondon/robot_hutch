#!/usr/bin/env python
import json

import uuid
from enum import Enum

import pika

__author__ = 'rogueleaderr'


class Procedure(Enum):
    FIB = "FIB"
    RAND = "RAND"


class Invocation:
    def __init__(self, procedure, *args):
        self.procedure = procedure
        self.args = args


class UnknownProcedure(Exception):
    pass


class Robot:

    def __init__(self, starts_alive, x_position, y_position):
        self.x_position = x_position
        self.y_position = y_position
        self.neighbor_message = []
        incoming_mailbox_name = "mailbox-{}x-{}y".format(x_position, y_position)
        self.incoming_mailbox_name = incoming_mailbox_name
        self.alive = starts_alive
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        queue_declare_result = self.channel.queue_declare(queue=incoming_mailbox_name, exclusive=True)
        self.incoming_mailbox = queue_declare_result.method.queue
        self.channel.basic_consume(self.on_receive, no_ack=True,
                                   queue=self.incoming_mailbox)

    def on_receive(self, ch, method, props, body):
        correlation_id = props.correlation_id
        if correlation_id in self.pending_requests:
            self.responses[correlation_id] = body
            self.pending_requests.remove(correlation_id)

class Sammy(Robot):
    def __init__(self):
        super(Sammy, self).__init__()
        self.pending_requests = set()
        self.responses = {}




    def call(self, invocation):
        # TODO guard bad invocation
        message = {'procedure': str(invocation.procedure.value)}
        if invocation.procedure == Procedure.FIB:
            n = invocation.args[0]
            message['data'] = n
        elif invocation.procedure == Procedure.RAND:
            pass
        else:
            raise UnknownProcedure

        correlation_id = str(uuid.uuid4())
        self.pending_requests.add(correlation_id)
        self.channel.basic_publish(exchange='',
                                   routing_key='rpc_queue',
                                   properties=pika.BasicProperties(
                                       reply_to=self.incoming_mailbox,
                                       correlation_id=correlation_id,
                                   ),
                                   body=json.dumps(message))
        while correlation_id not in self.responses:
            self.connection.process_data_events()
        return int(self.responses[correlation_id])


fibonacci_rpc = Sammy()

print(" [x] Requesting fib(30)")

for i in range(30):
    response = fibonacci_rpc.call(Invocation(Procedure.FIB, i))
    print(" [.] Got %r" % response)

for i in range(30):
    response = fibonacci_rpc.call(Invocation(Procedure.RAND))
    print(" [.] Got %r" % response)
