import logging

logging.basicConfig(
    level=logging.WARN,
    format='%(asctime)s | %(name)s > %(message)s',
    datefmt='%d.%m.%Y %H:%M:%S'
)


logger = logging.getLogger('serializer')
logger.setLevel(logging.INFO)

