# !/usr/bin/env python
import json

__author__ = 'rogueleaderr'

import pika
import random

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

channel = connection.channel()

channel.queue_declare(queue='rpc_queue')


def fib(n):
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fib(n - 1) + fib(n - 2)


def randomize():
    return random.randint(100, 200)


def on_request(ch, method, props, body):
    message = json.loads(body)
    print(message)
    procedure_name = message['procedure']

    if procedure_name == 'FIB':
        n = int(message['data'])
        print(" [.] fib(%s)" % n)
        response = fib(n)
    else:
        response = randomize()

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id=props.correlation_id),
                     body=str(response))
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(on_request, queue='rpc_queue')

print(" [x] Awaiting RPC pending_requests")
channel.start_consuming()
