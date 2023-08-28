import json


class Task:
    '''Task is the fundamental unit of work to interact with rabbitmq.

    Args:
        boi_id str: ...
        meta str: A description of the alert to be sent.
        qname str: ...
        '''
    def __init__(self):
        self.boi_id: str = ''
        self.channel_id: str = ''
        self.network_id: str = ''
        self.project_id: str = ''
        self.meta: str = ''
        self.qname: str = ''

    def to_dict(self):
        ret = {}
        ret['boi_id'] = self.boi_id if self.boi_id else None
        ret['channel_id'] = self.channel_id if self.channel_id else None
        ret['network_id'] = self.network_id if self.network_id else None
        ret['project_id'] = self.project_id if self.project_id else None
        ret['meta'] = self.meta if self.meta else None
        ret['qname'] = self.qname if self.qname else None
        return ret

    def __str__(self):
        return str(self.to_dict())

    def dumps_data(self):
        return json.dumps(self.to_dict())

    @property
    def next_q(self) -> str:
        if self.qname == 'for_shipper':
            return 'for_charger'
        return ''

    def load_from_body(self, body):
        '''
        Args:
            body List(byte): The message from rabbitmq.

        Returns:
            Task: The message from rabbitmq, converted into a processable Task
        object.
        '''
        decoded = json.loads(body.decode('utf-8'))

        self.boi_id = decoded.get('boi_id', '')
        self.channel_id = decoded.get('channel_id', '')
        self.network_id = decoded.get('network_id', '')
        self.project_id = decoded.get('project_id', '')
        self.meta = decoded.get('meta', '')
        self.qname = decoded.get('qname', '')
