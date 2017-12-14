import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s > %(message)s',
    datefmt='%d.%m.%Y %H:%M:%S'
)


logger = logging.getLogger('serializer:test')
logger.setLevel(logging.INFO)

