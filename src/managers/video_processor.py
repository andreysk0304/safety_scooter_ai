import os
import cv2
import logging

from typing import Optional
from ultralytics import YOLO
from ultralytics.engine.results import Results

from src.violation_detector import detect_violation, Violation
from src.managers.s3client import S3Client

logger = logging.getLogger(__name__)


class VideoProcessor:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model: Optional[YOLO] = None
        self.model_loaded = False

        self._load_model()


    def _load_model(self):
        try:
            logger.info(f"Загружаем модель {self.model_path}...")

            self.model = YOLO(self.model_path)
            self.model_loaded = True

            logger.info(f"Модель загружена успешно")

        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
            self.model_loaded = False

            raise


    def process_video_from_s3(self, bucket: str, key: str, aws_access_key_id: Optional[str] = None, aws_secret_access_key: Optional[str] = None, aws_region: str = "ru-1", s3_endpoint_url: Optional[str] = None) -> dict[int, set[Violation]]:
        if not self.model_loaded:
            raise RuntimeError("Модель не загружена")

        s3_client = S3Client(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_region=aws_region,
            s3_endpoint_url=s3_endpoint_url
        )

        tmp_path = s3_client.download_video(bucket, key)

        try:
            violations = self._process_video_file(tmp_path)
            return violations
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                logger.info(f"Временный файл видео удален")


    def process_video_from_local(self, video_path: str) -> dict[int, set[Violation]]:
        if not self.model_loaded:
            raise RuntimeError("Модель не загружена")

        return self._process_video_file(video_path)


    def _process_video_file(self, video_path: str) -> dict[int, set[Violation]]:
        logger.info(f"Начинаем обработку видео: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Не удалось открыть видео: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()

        logger.info(f"Видео: {total_frames} кадров, {fps:.2f} FPS")

        results: list[Results] = self.model.track(
            source=video_path,
            stream=True,
            verbose=False
        )

        violations: dict[int, set[Violation]] = {}
        frame_count = 0

        for result in results:
            frame_count += 1

            frame_violations = detect_violation(result)

            if frame_violations:
                for obj, viols in frame_violations.items():
                    if obj.id not in violations:
                        violations[obj.id] = viols
                    else:
                        violations[obj.id] = violations[obj.id].union(viols)

        logger.info(f"Обработка завершена: {frame_count} кадров")

        return violations