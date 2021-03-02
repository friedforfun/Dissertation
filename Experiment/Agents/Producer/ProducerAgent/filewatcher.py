import time

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from AgentBase.Utils.Logging import logger

class FileCreationWatcher:
    def __init__(self):
        self.src_path = './logs'
        self.event_handler = FileCreationEvent()
        self.event_observer = Observer()
        self._running = True
        self.path = None
        self.onnx_path = None

    def add_redis_to_event_handler(self, connection_manager):
        assert callable(getattr(connection_manager, 'set_onnx', None))
        assert callable(getattr(connection_manager, 'set_output', None))

        self.event_handler = FileCreationEvent(redis=connection_manager)
        logger.info('ONNX path will be sent to redis on_created event')


    def terminate(self):
        logger.debug('TERMINATING WATCHER CALL')
        self.path = self.event_handler.checkpoint_path
        self.onnx_path = self.event_handler.onnx_path
        logger.debug('WATCHER CHECKPOINT: {}'.format(self.path))
        logger.debug('WATCHER ONNX: {}'.format(self.onnx_path))
        self._running = False

    def run(self):
        self.start()
        try:
            while self._running:
                #logger.debug('Checking...')
                time.sleep(2)
        except KeyboardInterrupt:
            logger.debug('Keyboard interrupted')

        finally:
            logger.debug('STOPPPING WATCHER')
            self.stop()

    def start(self):
        self.schedule()
        self.event_observer.start()

    def stop(self):
        self.event_observer.stop()
        self.event_observer.join()
        

    def schedule(self):
        self.event_observer.schedule(
            self.event_handler,
            self.src_path,
            recursive=True
  )


class FileCreationEvent(PatternMatchingEventHandler):
    def __init__(self, redis=None):
        super(FileCreationEvent, self).__init__()
        self._ignore_directories = False
        #self._patterns = '*checkpoint.pth.tar'
        self.checkpoint_path = None
        self.onnx_path = None
        self.redis = redis


    def on_created(self, event):
        #logger.debug('On Created EVENT FIRED')
        #print(event.src_path)
        path = event.src_path
        if 'checkpoint.pth.tar' in path:
            #print('save this path: {}'.format(path))
            self.checkpoint_path = path
        if 'onnx' in path:
            print('ONNX detected: {}'.format(path))
            self.onnx_path = path
            
            # Needed to get the path out when using wandb
            # if the event has a reference to the connection manager:
            if self.redis is not None:
                self.redis.set_onnx(path)


        elif path.endswith('onnx'):
            print('endswith ONNX detected')
            self.onnx_path = path


    def on_any_event(self, event):
        path = event.src_path
        if 'output.log' in path:
            print('WANDB output log file: {}'.format(path))
            if self.redis is not None:
                self.redis.set_output(path)

    def on_moved(self, event):
        return super().on_moved(event)

    def on_deleted(self, event):
        return super().on_deleted(event)

    def on_modified(self, event):
        #logger.debug('File modivied event')
        return super().on_modified(event)
