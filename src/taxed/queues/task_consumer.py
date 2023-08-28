from taxed.core import plog
from taxed.queues.rabbit_transit import RabbitTransit


class TaskConsumer:
    '''TaskConsumer is created and set to listen forever to a queue.'''
    def __init__(
        self,
        queue_name: str,
        rab_host: str,
        rab_password: str,
        rab_user: str,
    ):
        self._rabbit_transit = RabbitTransit(
            rab_host=rab_host,
            rab_password=rab_password,
            rab_user=rab_user,
            queue_name=queue_name,
            queue_type='consumer',
        )

    def register_callback(self, callback):
        self._rabbit_transit.register_callback(callback)

    def listen_forever(self):
        try:
            self._rabbit_transit.listen_forever()
        except KeyboardInterrupt:
            plog.debug('Interrupt detected! Closing queue...')
            self._rabbit_transit.close()
            plog.debug('Queue closed.')
