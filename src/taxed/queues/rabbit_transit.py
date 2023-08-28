'''rabbit_transit contains most or all of the low level code needed to deal with
a rabbitmq connection. pika is the library used here.

Note that queues have the name format: for_{microservice_name}
'''
import pika
from pika import spec
# import ssl
from typing import Callable, List

from taxed.core import plog
from taxed.queues.task import Task
from taxed.state import conf


def grab_channel(rab_host: str, rab_password: str, rab_user: str):
    # context = ssl.create_default_context(
        # cafile='/papi/certs/ca-cert.pem')
    # context.load_cert_chain('/papi/certs/rabclient-cert.pem',
                            # '/papi/certs/rabclient-key.pem')
    # ssl_options = pika.SSLOptions(context, 'localhost')

    credentials = pika.PlainCredentials(rab_user, rab_password)
    parameters = pika.ConnectionParameters(
        host=rab_host,
        port=5672,
        credentials=credentials,
        # port=5671,
        # ssl_options=ssl_options,
    )
    connection = pika.BlockingConnection(parameters)
    return connection.channel()


def publish_task(task: Task, queue_name: str):
    task.qname = queue_name
    rabchannel = grab_channel(conf.rabbit_host,
                              conf.rabbit_pass,
                              conf.rabbit_user)
    rabchannel.queue_declare(queue=queue_name, durable=True)
    rabchannel.basic_publish(
        exchange=conf.rabbit_dn,
        routing_key=queue_name,
        body=task.dumps_data(),
        properties=pika.BasicProperties(
            delivery_mode=spec.PERSISTENT_DELIVERY_MODE
        ))


#TODO: connection.close()??
class RabbitTransit:
    def __init__(self,
                 rab_host,
                 rab_password,
                 rab_user,
                 queue_name,
                 queue_type,
                 exchange='',
                 ):
        self._exchange = exchange
        self._rab_host = rab_host
        self._rab_password = rab_password
        self._rab_user = rab_user
        # _callbacks are a list of functions that will be called by a
        # TaskConsumer when a Task is found on a queue. Because it
        # is a list, they will be called in order.
        self._callbacks: List[Callable] = []

        # valie_queue_names restricts the queue names used, to prevent errors
        # and guide development.
        valid_queue_names = [
            'for_shipper',
            'for_charger',
            'for_alerter',
        ]
        if queue_name not in valid_queue_names:
            raise RuntimeError(f'ERROR: invalid queue_name: {queue_name}')
        self._queue_name = queue_name

        self.rabchannel = grab_channel(rab_host, rab_password, rab_user)
        self.rabchannel.queue_declare(queue=self._queue_name, durable=True)

        def callback_hook(ch, method, properties, body):
            '''Processes all registered callbacks for a queue type.'''
            plog.d('Received %r' % body)
            task = Task()
            task.load_from_body(body)
            for fun in self._callbacks:
                fun(task)

            plog.d('DONE - sending next step to rabbitmq if exists')
            self.start_next_step_if_exists(task)
            ch.basic_ack(delivery_tag = method.delivery_tag)

        if queue_type == 'consumer':
            #TODO: disable auto_ack - ack a queue only after successful
            # job completion, and maybe other error handling
            self.rabchannel.basic_consume(queue=self._queue_name,
                                          on_message_callback=callback_hook)
        elif queue_type == 'producer':
            pass
        else:
            raise RuntimeError('queue_type must be consumer or producer')

    def register_callback(self, callback):
        self._callbacks.append(callback)

    def listen_forever(self):
        self.rabchannel.start_consuming()

    def close(self):
        self.rabchannel.close()

    def start_next_step_if_exists(self, task: Task):
        '''Continues execution of the Task by placing it on the next queue. If
        there are no more queues in the Task, then the Task is done.'''
        if task.next_q:
            publish_task(task, task.next_q)
