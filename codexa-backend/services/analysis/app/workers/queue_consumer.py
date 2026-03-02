from __future__ import annotations

import json
import logging
import time

from libs.common.aws import sqs_client
from libs.common.config import settings
from libs.common.db import SessionLocal
from services.analysis.app.workers.analysis_worker import run_job

logger = logging.getLogger(__name__)


def consume_once():
    if not settings.sqs_queue_url:
        logger.error("SQS_QUEUE_URL is not set")
        return
    client = sqs_client()
    response = client.receive_message(
        QueueUrl=settings.sqs_queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10,
    )
    messages = response.get("Messages", [])
    if not messages:
        return
    for message in messages:
        receipt = message["ReceiptHandle"]
        body = json.loads(message["Body"])
        job_id = body.get("job_id")
        if not job_id:
            client.delete_message(QueueUrl=settings.sqs_queue_url, ReceiptHandle=receipt)
            continue
        session = SessionLocal()
        try:
            run_job(int(job_id), session)
            client.delete_message(QueueUrl=settings.sqs_queue_url, ReceiptHandle=receipt)
        except Exception:
            logger.exception("Failed to process job %s", job_id)
        finally:
            session.close()


def main():
    logger.info("Starting SQS consumer")
    while True:
        consume_once()
        time.sleep(1)


if __name__ == "__main__":
    main()
