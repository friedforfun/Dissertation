import time
from AgentBase.redismanager import RedisConnectionManager as RCM

class RedisConnectionManager(RCM):
    def __init__(self, agent_id, host, port=6379, db=0, password=None, message_fn=None):
        super(RedisConnectionManager, self).__init__(agent_id, host, redis_port=port, db=db, password=password, message_fn=message_fn)
        self.subscribe('{}_result_channel'.format(self.agent_id))

    def set_output(self, output):
        """Set the output path key for the agent

        Args:
            output (str): path to output log file
        """
        self.connection.set('{}_output_log_path'.format(self.agent_id), output)

    def get_output(self):
        """Gets the log file output path

        Returns:
            str: Path to the output log
        """
        return self.connection.get('{}_output_log_path'.format(self.agent_id))

    def set_onnx(self, onnx):
        """Set the agents onnx path key

        Args:
            onnx (str): The path of the onnx file
        """
        self.connection.set('{}_onnx_path'.format(self.agent_id), onnx)


    def get_onnx(self):
        """Get the onnx path

        Returns:
            str: The path to the onnx file
        """
        return self.connection.get('{}_onnx_path'.format(self.agent_id))


    def set_checkpoint(self, checkpoint):
        self.connection.set('{}_checkpoint'.format(self.agent_id), checkpoint)

    def get_checkpoint(self):
        return self.connection.get('{}_checkpoint'.format(self.agent_id))

    def publish_model(self, message):
        """Publish the details of the model so the consumer agent can download and run the benchmark

        :param message: name of onnx model
        :type message: string
        """
        # Message should contain: agent id, model path, model storage host, model UUID
        self.connection.publish('model_channel', message)


    def listen_blocking(self, message_fn, exit_fn):
        """Listens on agents result channel

        Args:
            message_fn (string -> Any): function to handle recived messages
            exit_fn (string -> bool): function to set the exit loop condition
        """
        exit_condition = False
        #print('Listening for message...')
        #print('On: {}'.format(self.sub))
        while not exit_condition:
            message = self.sub.get_message()
            if message:
                #print('Got message back')
                message_type = message.get('type')
                if message_type == 'message':
                    message_fn(message.get('data'))
                    exit_condition = exit_fn(message.get('data'))
            time.sleep(2)


                
        