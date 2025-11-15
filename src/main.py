import sys
import logging

from src.utils.config import (
    MODEL_PATH, 
    CHECK_INTERVAL, 
    DATABASE_URL,
    S3_BUCKET,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION
)

from src.ai_worker import AiWorker

logger = logging.getLogger(__name__)


def main():
    try:
        worker = AiWorker(
            database_url=DATABASE_URL,
            model_path=MODEL_PATH,
            s3_bucket=S3_BUCKET,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            aws_region=AWS_REGION
        )

        worker.run_forever(check_interval=CHECK_INTERVAL)

    except KeyboardInterrupt:
        logger.info("\nРабота завершена")

    except Exception as e:
        logger.error(f"\nКритическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()