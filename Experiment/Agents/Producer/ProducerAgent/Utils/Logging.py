import logging
import functools
import sys

logging.basicConfig(format='[ %(levelname)s ] %(message)s', level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger('ProducerAgent')


def debug(func):
    """Decorator to show debug log messages
    Args:
        func (Any -> Any): Any function
    """
    @functools.wraps(func)
    def inner(*args, **kwargs):
        from ProducerAgent.Utils.Logging import logger, logging
        logger.setLevel(logging.DEBUG)
        return func(*args, **kwargs)

    #logger.setLevel(logging.INFO)
    return inner