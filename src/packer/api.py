import requests
import json

import logging
logger = logging.getLogger(__name__)

def get(url: str) -> dict:
    r = requests.get(url)
    try:
        return r.json()
    except Exception:
        logger.error("API GET call was unsuccessful!")
        logger.error(f"URL: {url}")
        logger.error(f"Return code: {r.status_code}")
        if r.text:
            logger.error("Response:")
            logger.error(r.text)

def post(url: str, data: dict) -> dict:
    r = requests.post(url, data=json.dumps(data), headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    try:
        return r.json()
    except Exception:
        logger.error("API POST call was unsuccessful!")
        logger.error(f"URL: {url}")
        logger.error(f"Return code: {r.status_code}")
        if r.text:
            logger.error("Response:")
            logger.error(r.text)
