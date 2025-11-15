import datetime
import logging

from time import sleep
from typing import Optional

from src.database_models import Applications, Verdicts
from src.managers.database import Database
from src.managers.video_processor import VideoProcessor

from sqlalchemy.orm import Session

from src.violation_detector import Violation, ViolationNames

logger = logging.getLogger(__name__)

VIOLATION_TYPE_MAP = {
    ViolationNames.more_than_one_people: "multiple_people_on_scooter",
    ViolationNames.zebra_crossing: "riding_on_zebra_crossing"
}

class AiWorker:
    def __init__(self,
        database_url: str,
        model_path: str,
        s3_bucket: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: str = "ru-central1"
    ) -> None:

        self.db = Database(database_url)
        self.processor = VideoProcessor(model_path)
        self.s3_bucket = s3_bucket
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region

        logger.info('AiWorker успешно инициализирован!')


    def get_pending_task(self, session: Session) -> Optional[Applications]:
        task = session.query(Applications).filter(
            Applications.status == 'pending',
            Applications.is_delete == False
        ).order_by(
            Applications.created_at
        ).with_for_update(
            skip_locked=True
        ).first()

        if task:
            task.status = 'processing'
            task.last_change = datetime.datetime.utcnow()
            session.commit()

            logger.info(f"Взята заявка #{task.id} в обработку")

        return task


    def process_task(self, task: Applications, session: Session):
        try:
            violations = self.processor.process_video_from_s3(
                bucket=self.s3_bucket,
                key=task.key,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                aws_region=self.aws_region
            )

            self._save_results(task, violations, session)

        except Exception as e:
            logger.error(f"Ошибка при обработке заявки #{task.id}: {e}\n")

            self._mark_as_failed(task, session)


    def _save_results(self, task: Applications, violations: dict[int, set[Violation]], session: Session):
        if violations:
            task.status = 'completed'
        else:
            task.status = 'no_violations'

        task.last_change = datetime.datetime.utcnow()

        for obj_id, viols in violations.items():
            for violation in viols:
                violation_type = VIOLATION_TYPE_MAP.get(
                    violation.violation_name,
                    violation.violation_name.value
                )

                coordinates_str = None
                if violation.global_coordinates:
                    coordinates_str = str(violation.global_coordinates)

                verdict = Verdicts(
                    application_id=task.id,
                    type=violation_type,
                    scooter_type=violation.scooter_name.value,  # Yandex/Whoosh/Urent
                    object_id=obj_id,  # ID объекта из YOLO tracking
                    timestamp=violation.time,  # Время в видео
                    coordinates=coordinates_str,  # Координаты
                    created_at=datetime.datetime.utcnow()
                )
                session.add(verdict)

        session.commit()


    def _mark_as_failed(self, task: Applications, session: Session):
        task.status = 'failed'
        task.last_change = datetime.datetime.utcnow()

        session.commit()


    def process_one_task(self) -> bool:
        with self.db.get_session() as session:
            task = self.get_pending_task(session)

            if not task:
                return False

            self.process_task(task, session)
            return True


    def run_forever(self, check_interval: int = 1):
        logger.info(f"AiWorker начал работу. Проверка БД каждые {check_interval} секунд")

        try:
            while True:
                processed = self.process_one_task()

                if not processed:
                    sleep(check_interval)

        except Exception as e:
            logger.error(f'Ошибка AiWorker: {e}')