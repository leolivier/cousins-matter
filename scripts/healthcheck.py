import os
import sys
import urllib.request
import logging

logger = logging.getLogger(__name__)

port = os.getenv("PORT", 9001)
for path in ["health", "qhealth"]:
  url = f"http://127.0.0.1:{port}/{path}/"
  logger.info("url =", url)
  # test the health check
  r = urllib.request.urlopen(url, timeout=5)
  if r.getcode() != 200:
    logger.error("url=", url, "code=", r.getcode(), "msg=", r.read().decode("utf-8"))
    sys.exit(1)

sys.exit(0)
