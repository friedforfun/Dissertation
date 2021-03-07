from time import sleep
from AgentBase.redismanager import RedisConnectionManager as RCM
import redis
from AgentBase.Utils.Logging import logger
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


class ConnectionController():
    def __init__(self, agent_id, host, port, db, password, message_fn):
        self.agent_id = agent_id
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.message_fn = message_fn

        self.connected = False

    def connect(self):
        try:
            self.conn = RedisConnectionManager(self.agent_id, self.host, self.port, self.db, self.password, self.message_fn)
            self.conn.connection.ping()
            self.connected = True
            self.conn.add_message_fn(self.message_fn)
        except redis.ConnectionError:
            self.connected = False


    def start(self):
        self.connect()
        while True:
            try:
                logger.debug('Starting listener')
                self.conn.run()
            except:
                logger.debug('Connection dropped... retrying...')
                # connection failed
                self.connected = False
                while not self.connected:
                    self.connect()
                    if not self.connected:
                        sleep(1)