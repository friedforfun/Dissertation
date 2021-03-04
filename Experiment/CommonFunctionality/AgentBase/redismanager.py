import redis

class RedisConnectionManager:
    def __init__(self, agent_id, redis_host, redis_port=6379, db=0, password=None, message_fn=None):
        """Redis connection manager for experiment agents

        :param agent_id: A unique identifier for this agent
        :type agent_id: str
        :param redis_host: The IPv4 address of the redis host
        :type redis_host: str
        :param redis_port: The port used for redis, defaults to 6379
        :type redis_port: int, optional
        :param db: The database to use with reids, defaults to 0
        :type db: int, optional
        :param password: Password for redis, defaults to None
        :type password: str, optional
        :param message_fn: Function to call on message recived by listener, defaults to None
        :type message_fn: byte str -> Any, optional
        """
        self.connection = redis.Redis(host=redis_host, port=redis_port, db=db, password=password)
        self.sub = self.connection.pubsub(ignore_subscribe_messages=True)
        self.agent_id = agent_id
        self.message_fn = message_fn


    def subscribe(self, channel):
        """Subscribe to tha channel

        :param channel: Channel identifier
        :type channel: str
        """
        self.sub.subscribe(channel)


    def add_message_fn(self, message_fn):
        """Pass a reference to a function to call when a message is recived

        :param message_fn: A function to call on message recieved, (takes message byte as an arg)
        :type message_fn: byte string -> Any
        """
        self.message_fn = message_fn


    def run(self):
        """Pass to a thread target to listen for messages

        :raises ValueError: No behaviour is defined when a message is recived
        """
        if self.message_fn is None:
            raise ValueError('No message handling function defined')

        self.listen_blocking(self.message_fn)


    def get_message(self):
        """Gets a message from the subscribed channel

        :return: message from redis
        :rtype: byte string or None
        """
        self.newest_message = self.sub.get_message()
        return self.newest_message


    def listen_blocking(self, message_fn):
        """Listens on agents subscribed channel

        Args:
            message_fn (string -> Any): function to handle recived messages
        """
        for message in self.sub.listen():
            message_type = message.get('type')
            if message_type == 'message':
                message_fn(message.get('data'))
        
        