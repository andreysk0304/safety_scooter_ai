import io
import tempfile
import boto3
import logging

from typing import Optional

logger = logging.getLogger(__name__)


class S3Client:
    def __init__(self, aws_access_key_id: Optional[str] = None, aws_secret_access_key: Optional[str] = None, aws_region: str = "ru-central1"):

        kwargs = {'region_name': aws_region}

        if aws_access_key_id and aws_secret_access_key:
            kwargs['aws_access_key_id'] = aws_access_key_id
            kwargs['aws_secret_access_key'] = aws_secret_access_key

        self.s3 = boto3.client('s3', **kwargs)


    def download_video(self, bucket: str, key: str) -> str:
        logger.info(f"Скачиваем видео по пути: s3://{bucket}/{key}")

        buffer = io.BytesIO()
        self.s3.download_fileobj(bucket, key, buffer)

        size_mb = buffer.tell() / (1024 * 1024)
        logger.info(f"Загружено: {size_mb:.2f} MB")

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tmp.write(buffer.getvalue())
        tmp.close()

        logger.info(f"Временный файл: {tmp.name}")

        return tmp.name