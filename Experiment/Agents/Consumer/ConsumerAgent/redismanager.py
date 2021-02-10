import redis

class RedisConnectionManager:
    def __init__(self, agent_id, host, port=6379, db=0, password=None):
        self.connection = redis.Redis(host=host, port=port, db=db, password=password)
        self.model = self.connection.pubsub(ignore_subscribe_messages=True)
        self.agent_id = agent_id
        self.model.subscribe('model_channel')
        self.message_fn = None

    def add_message_fn(self, message_fn):
        self.message_fn = message_fn

    def run(self):
        if self.message_fn is None:
            raise ValueError('No message handling function defined')

        self.listen_blocking(self.message_fn)


    def publish_model_result(self, message, agent_id):
        """Publish the details of the model so the consumer agent can download and run the benchmark

        :param message: name of onnx model
        :type message: string
        """
        # Message should contain: modelUUID, latency, accuracy, throughput
        self.connection.publish('{}_result_channel'.format(agent_id), message)


    def get_message(self):
        self.newest_message = self.model.get_message()
        return self.newest_message


    def listen_blocking(self, message_fn):
        """Listens on agents result channel

        Args:
            message_fn (string -> Any): function to handle recived messages
        """
        for message in self.model.listen():
            message_type = message.get('type')
            if message_type == 'message':
                message_fn(message.get('data'))
        