# _includes/logging.py
import sys
from loguru import logger
import asyncio


def custom_print(msg):
    sys.stdout.write(msg)
    sys.stdout.flush()

def setup_logging():
    logger.remove()

    logger.add(lambda msg: custom_print(msg), level="INFO",
               format="             INFO | <level>{message}</level>",
               filter=lambda record: record["level"].name == "INFO", colorize=True)

    logger.level("AUTHENTICATION", no=21, color="<cyan>")
    logger.add(lambda msg: custom_print(msg), level="AUTHENTICATION",
               format="   AUTHENTICATION | <level>{message}</level>",
               filter=lambda record: record["level"].name == "AUTHENTICATION", colorize=True)

    logger.level("PING", no=22, color="<blue>")
    logger.add(lambda msg: custom_print(msg), level="PING",
               format="             PING | <level>{message}</level>",
               filter=lambda record: record["level"].name == "PING", colorize=True)

    logger.level("PONG", no=23, color="<green>")
    logger.add(lambda msg: custom_print(msg), level="PONG",
               format="             PONG | <level>{message}</level>",
               filter=lambda record: record["level"].name == "PONG", colorize=True)

    logger.add(lambda msg: custom_print(msg), level="ERROR",
               format="            ERROR | <level>{message}</level>",
               filter=lambda record: record["level"].name == "ERROR", colorize=True)

    logger.add(lambda msg: custom_print(msg), level="WARNING",
               format="          WARNING | <level>{message}</level>",
               filter=lambda record: record["level"].name == "WARNING", colorize=True)

    logger.level("STATUS", no=25, color="<magenta>")
    logger.add(lambda msg: custom_print(msg), level="STATUS",
               format="           STATUS | <level>{message}</level>",
               filter=lambda record: record["level"].name == "STATUS", colorize=True)

async def log_status(stats, removed_proxies):
    while True:
        logger.log("STATUS", f"Current Stats - Active: {stats['active_connections']}, Pings: {stats['pings']}, Pongs: {stats['pongs']}, Removed: {removed_proxies[0]}") # Added active_connections
        await asyncio.sleep(5)  # Adjust frequency as needed