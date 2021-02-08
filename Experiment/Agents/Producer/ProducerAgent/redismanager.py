import redis

class RedisConnectionManager:
    def __init__(self, agent_id, host, port=6379, db=0, password=None):
        self.connection = redis.Redis(host=host, port=port, db=db, password=password)
        self.sub = self.connection.pubsub(ignore_subscribe_messages=True)
        self.agent_id = agent_id
        self.sub.subscribe('{}_result_channel'.format(self.agent_id))
        self.sub.subscribe('{}_onnx_path'.format(self.agent_id))

    def set_onnx(self, onnx):
        self.connection.set('{}_onnx_path'.format(self.agent_id), onnx)

    def get_onnx(self):
        return self.connection.get('{}_onnx_path'.format(self.agent_id))

    def publish_model(self, message):
        """Publish the details of the model so the consumer agent can download and run the benchmark

        :param message: name of onnx model
        :type message: string
        """
        # Message should contain: agent id, model path, model storage host, model UUID
        self.connection.publish('model_channel', message)


    def publish_message(self, channel, message):
        self.connection.publish(channel, message)


    def get_message(self):
        # message should contain: model UUID, latency, accuracy, throughput
        self.newest_message = self.sub.get_message()
        return self.newest_message


    def listen_blocking(self, message_fn, exit_fn):
        """Listens on agents result channel

        Args:
            message_fn (string -> Any): function to handle recived messages
            exit_fn (string -> bool): function to set the exit loop condition
        """
        exit_condition = False
        while not exit_condition:
            message = self.sub.get_message()
            if message:
                message_type = message.get('type')
                if message_type == 'message':
                    message_fn(message.get('data'))
                    exit_condition = exit_fn(message.get('data'))
                
        