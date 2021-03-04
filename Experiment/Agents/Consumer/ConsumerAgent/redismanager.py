from AgentBase.redismanager import RedisConnectionManager as RCM

class RedisConnectionManager(RCM):
    def __init__(self, agent_id, host, port=6379, db=0, password=None, message_fn=None):
        super(RedisConnectionManager, self).__init__(agent_id, host, redis_port=port, db=db, password=password, message_fn=message_fn)
        self.subscribe('model_channel')

    def publish_model_result(self, message, agent_id):
        """Publish the details of the model so the consumer agent can download and run the benchmark

        :param message: name of onnx model
        :type message: string
        """
        # Message should contain: modelUUID, latency, accuracy, throughput
        self.connection.publish('{}_result_channel'.format(agent_id), message)

        