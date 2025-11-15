from enum import Enum
from typing import Any
from ultralytics.engine.results import Results


class ModelObject(str, Enum):
    yandex = "Yandex"
    whoosh = "Whoosh"
    urent = "Urent"
    deck = "Deck"
    foot = "Foot"
    head = "Head"
    zebra = "Zebra"
    
    def __repr__(self):
        return self.name
    
    def __str__(self):
        return self.name


class ViolationNames(str, Enum):
    more_than_one_people = "Нарушение: Два или более человека на самокате"
    zebra_crossing = "Нарушение: Езда по пешеходному переходу не спешиваясь с СИМ"
    
    def __repr__(self):
        return self.name
    
    def __str__(self):
        return self.name


class Violation:
    def __init__(
        self, 
        violation_name: ViolationNames,
        scooter_name: ModelObject,
        global_coordinates: Any = None, 
        time: Any = None
    ):
        self.violation_name = violation_name
        self.scooter_name = scooter_name
        self.global_coordinates = global_coordinates
        self.time = time
    
    def __hash__(self):
        return hash(self.violation_name.name)
    
    def __eq__(self, other):
        return self.violation_name.name == other.violation_name.name
    
    def __repr__(self):
        return f"[{self.time}]: {self.violation_name} in {self.global_coordinates} on {self.scooter_name} scooter"


class Dot:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


class DetectedObject:
    def __init__(
        self, 
        _id: int, 
        name: ModelObject, 
        cords: tuple[float, float, float, float]
    ):
        self.id = int(_id)
        self.name = name
        self.cords = cords
        self.top_left = Dot(cords[0], cords[1])
        self.bottom_right = Dot(cords[2], cords[3])
        self.w = abs(cords[0] - cords[2])
        self.h = abs(cords[1] - cords[3])
        self.center = Dot(self.top_left.x + self.w / 2, self.top_left.y + self.h / 2)
    
    def __repr__(self):
        return f"{self.name}[{self.id}]: {self.cords}"

MODEL_OBJECTS_FROM_STRING = {
    "Yandex": ModelObject.yandex,
    "Whoosh": ModelObject.whoosh,
    "Urent": ModelObject.urent,
    "Deck": ModelObject.deck,
    "Foot": ModelObject.foot,
    "Head": ModelObject.head,
    "Zebra": ModelObject.zebra
}

OBJECT_ID = {
    ModelObject.yandex: 0,
    ModelObject.whoosh: 1,
    ModelObject.urent: 2,
    ModelObject.deck: 3,
    ModelObject.foot: 4,
    ModelObject.head: 5,
    ModelObject.zebra: 6
}

SCOOTERS = [ModelObject.yandex, ModelObject.urent, ModelObject.whoosh]

def detect_violation(image: Results) -> dict[DetectedObject, set[Violation]] | None:
    """
    Детектировать нарушения на одном кадре
    
    :param image: Результат детекции YOLO
    :return: Словарь {объект: множество нарушений} или None
    """
    objects_dict: dict[str, list[DetectedObject]] = dict()
    violations: dict[DetectedObject, set[Violation]] = dict()
    
    # Инициализируем словарь для всех типов объектов
    for key in MODEL_OBJECTS_FROM_STRING.values():
        objects_dict[key] = []
    
    # Проверяем что есть детекции с tracking
    if image.boxes is None or image.boxes.is_track is False:
        return None
    
    names = image.names
    cords = image.boxes.xyxy.tolist()
    classes = image.boxes.cls.tolist()
    ids = image.boxes.id.tolist()
    
    # Собираем все детектированные объекты
    for i in range(len(cords)):
        obj = DetectedObject(
            ids[i], 
            MODEL_OBJECTS_FROM_STRING[names[classes[i]]], 
            cords[i]
        )
        objects_dict.get(obj.name).append(obj)
    
    # Проверяем нарушения для каждого самоката
    for scooter_type in SCOOTERS:
        for scooter in objects_dict[scooter_type]:
            
            # Ищем деку самоката
            deck = None
            for checked_deck in objects_dict[ModelObject.deck]:
                if (scooter.top_left.x < checked_deck.center.x < scooter.bottom_right.x 
                    and scooter.center.y < checked_deck.center.y 
                    and scooter.h > checked_deck.h):
                    deck = checked_deck
                    break
            
            if deck is None:
                continue
            
            # Считаем головы, ноги, зебры
            head_count, foot_count, zebra_count = 0, 0, 0
            
            for cur_head in objects_dict[ModelObject.head]:
                if scooter.top_left.x < cur_head.top_left.x < scooter.bottom_right.x:
                    head_count += 1
            
            for cur_foot in objects_dict[ModelObject.foot]:
                if (deck.top_left.x < cur_foot.center.x < deck.bottom_right.x 
                    and deck.center.y > cur_foot.center.y):
                    foot_count += 1
            
            for cur_zebra in objects_dict[ModelObject.zebra]:
                if (scooter.center.x > cur_zebra.center.x 
                    and scooter.center.y < cur_zebra.center.y 
                    and (cur_zebra.w > scooter.w or cur_zebra.h > scooter.h)):
                    zebra_count += 1
            
            # Определяем нарушения
            violations[scooter] = set()
            
            if foot_count > 1 or head_count > 1:
                violations[scooter].add(
                    Violation(ViolationNames.more_than_one_people, scooter_type)
                )
            
            elif zebra_count > 0 and foot_count > 0:
                violations[scooter].add(
                    Violation(ViolationNames.zebra_crossing, scooter_type)
                )
    
    return violations

