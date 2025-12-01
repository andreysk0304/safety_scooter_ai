# NeyroService - AI Worker для детекции нарушений на самокатах

Сервис для автоматической обработки видео с камер и детекции нарушений правил использования самокатов (Yandex, Whoosh, Urent).

## Технологии

- **Python 3.11**
- **YOLOv11** (Ultralytics)
- **PyTorch** для нейросетевой обработки
- **OpenCV** для работы с видео
- **SQLAlchemy** для работы с PostgreSQL
- **Boto3** для работы с S3

## Структура проекта

```
NeyroService/
├── src/
│   ├── main.py                  # Точка входа
│   ├── ai_worker.py             # Основной worker
│   ├── violation_detector.py   # Логика детекции нарушений
│   ├── database_models.py       # SQLAlchemy модели
│   ├── managers/
│   │   ├── database.py          # Менеджер БД
│   │   ├── s3client.py          # S3 клиент
│   │   └── video_processor.py   # Обработка видео
│   └── utils/
│       └── config.py            # Конфигурация
├── models/
│   └── best.pt                  # YOLO модель
├── requirements.txt             # Python зависимости
├── Dockerfile                   # Multi-stage Docker образ
├── .dockerignore                # Исключения для Docker
└── .gitignore                   # Git исключения

```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|-----------|----------|--------------|
| `DATABASE_URL` | URL подключения к PostgreSQL | - |
| `MODEL_PATH` | Путь к YOLO модели | `models/best.pt` |
| `CHECK_INTERVAL` | Интервал проверки БД (сек) | `10` |
| `S3_BUCKET` | Имя S3 bucket | - |
| `AWS_ACCESS_KEY_ID` | AWS Access Key | - |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Key | - |
| `AWS_REGION` | AWS регион | `ru-1` |
| `S3_ENDPOINT_URL` | URL S3-совместимого хранилища | - |

## База данных

Структура таблиц:

### `applications`
- `id` - ID заявки
- `user_id` - ID пользователя
- `key` - S3 ключ видео
- `status` - Статус: pending/processing/completed/failed/no_violations
- `gps_longitude`, `gps_width` - GPS координаты
- `record_time` - Время записи
- `is_delete` - Флаг удаления
- `created_at`, `last_change` - Временные метки

### `verdicts`
- `id` - ID вердикта
- `application_id` - Ссылка на заявку
- `type` - Тип нарушения
- `scooter_type` - Тип самоката (Yandex/Whoosh/Urent)
- `object_id` - ID объекта из YOLO tracking
- `timestamp` - Время в видео
- `coordinates` - Координаты на кадре
- `created_at` - Время создания

## Логика работы

1. Worker проверяет БД каждые N секунд (CHECK_INTERVAL)
2. Берет первую заявку со статусом `pending`
3. Скачивает видео из S3
4. Обрабатывает видео через YOLO с tracking
5. Детектирует нарушения на каждом кадре
6. Сохраняет результаты в таблицу `verdicts`
7. Обновляет статус заявки: `completed` или `no_violations`
8. При ошибке ставит статус `failed`

### Два человека на самокате
- Детектируется > 1 головы или > 1 пары ног на самокате

### Езда по пешеходному переходу
- Детектируется самокат на зебре с человеком (не спешиваясь)

## Лицензия

### YOLO (Ultralytics)

В данном проекте используется модель **YOLO11** и библиотека **Ultralytics**, распространяемые под лицензией  
**GNU Affero General Public License v3.0 (AGPL-3.0)**.

Для **некомерческого (учебного/исследовательского) использования** мы опираемся на условия AGPL-3.0:  
вы можете использовать, изменять и запускать данное ПО, при условии что при его распространении
или предоставлении как сетевого сервиса пользователям:

- исходный код проекта (включая модификации и производные работы, такие как обученные веса моделей)  
  доступен пользователям под той же лицензией AGPL-3.0;
- сохраняются уведомления об авторских правах и текст лицензии.

Полный текст лицензии Ultralytics YOLO:  
- Лицензия в репозитории Ultralytics: https://github.com/ultralytics/ultralytics/blob/main/LICENSE  
- Обзор вариантов лицензирования (AGPL-3.0 / Enterprise): https://www.ultralytics.com/license