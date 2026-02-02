"""Test logging configuration"""
import sys
import logging
import time

# Test 1: Verify basicConfig can be called
print("=" * 60)
print("Test 1: Basic logging configuration")
print("=" * 60)

logging.basicConfig(
    level=logging.INFO,
    format='%(relativeCreated)8d ms [%(name)s] %(message)s',
    handlers=[
        logging.FileHandler("test_logging.log", mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("TestLogger")

logger.info("Message 1: Start")
time.sleep(0.1)
logger.info("Message 2: After 100ms")
time.sleep(0.2)
logger.info("Message 3: After 200ms more")

print("\n" + "=" * 60)
print("Test 2: Import CC_Main and test its logger")
print("=" * 60)

# Reset logging for clean test
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

from CC_Main import logger as cc_logger

cc_logger.info("CC_Main logger test 1")
time.sleep(0.05)
cc_logger.info("CC_Main logger test 2 after 50ms")

print("\n" + "=" * 60)
print("✓ Test completed. Check test_logging.log and chromacloud.log")
print("=" * 60)
