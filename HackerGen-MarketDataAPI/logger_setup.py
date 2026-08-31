import logging
import os

os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("HackerGenAPI")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("logs/hackergen_api.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.propagate = False

# Third-party libraries ka shor aur sensitive data band karo
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("pyquotex").setLevel(logging.WARNING)