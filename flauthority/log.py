import logging

def setup_custom_logger(logging_level):
    logger = logging.getLogger('flauthority')
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if logging_level == "debug":
        logger.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
    elif logging_level == "info":
        logger.setLevel(logging.INFO)
        ch.setLevel(logging.INFO)
    elif logging_level == "error":
        logger.setLevel(logging.ERROR)
        ch.setLevel(logging.ERROR)
    return logger
