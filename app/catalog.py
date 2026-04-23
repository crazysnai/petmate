from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Plant:
    key: str
    name: str
    category: str
    confidence: float
    knowledge: str
    safety_tip: str
    food_key: str
    food_name: str
    xp: int = 10


@dataclass(frozen=True)
class AnimalClue:
    key: str
    name: str
    category: str
    rarity: str
    knowledge: str
    safety_tip: str
    favorite: str
    habitat: str
    greeting: str
    friendship: int = 25
    xp: int = 15


PLANTS: list[Plant] = [
    Plant(
        key="dandelion",
        name="蒲公英",
        category="开花植物",
        confidence=0.91,
        knowledge="蒲公英的种子会借助风传播，像小伞一样飞到新的地方。",
        safety_tip="只观察和拍照，不随意采摘或入口。",
        food_key="sun_nectar",
        food_name="阳光花蜜",
    ),
    Plant(
        key="clover",
        name="三叶草",
        category="草本植物",
        confidence=0.88,
        knowledge="三叶草常见的叶片由三片小叶组成，是观察复叶结构的好材料。",
        safety_tip="观察叶片形状即可，不要在草丛里翻找昆虫。",
        food_key="fresh_leaf",
        food_name="清新嫩叶",
    ),
    Plant(
        key="plane_leaf",
        name="梧桐叶",
        category="乔木叶片",
        confidence=0.86,
        knowledge="梧桐叶宽大，能帮助树木获得阳光，也能形成树荫。",
        safety_tip="注意脚下和车辆，只捡拾地上的落叶观察。",
        food_key="shade_fruit",
        food_name="树荫果实",
    ),
]


ANIMAL_CLUES: list[AnimalClue] = [
    AnimalClue(
        key="sparrow",
        name="麻雀线索",
        category="鸟类",
        rarity="common",
        knowledge="麻雀常在灌木、草地和屋檐附近活动，会寻找种子和小虫。",
        safety_tip="远距离观察，不追赶、不投喂。",
        favorite="阳光花蜜",
        habitat="草地边缘和灌木旁",
        greeting="麻雀在远处跳了两下，像是在回应你的观察。",
    ),
    AnimalClue(
        key="butterfly",
        name="蝴蝶线索",
        category="昆虫",
        rarity="common",
        knowledge="蝴蝶会在花朵附近吸食花蜜，也是植物传粉的帮手。",
        safety_tip="不要触碰翅膀，保持距离观察飞行路线。",
        favorite="清新嫩叶",
        habitat="花丛和草地",
        greeting="蝴蝶绕着花朵飞了一圈，留下新的观察线索。",
    ),
    AnimalClue(
        key="snail",
        name="蜗牛线索",
        category="软体动物",
        rarity="uncommon",
        knowledge="蜗牛喜欢潮湿环境，雨后更容易看到活动痕迹。",
        safety_tip="观察后不要带回家，也不要放到危险路面。",
        favorite="树荫果实",
        habitat="潮湿树荫和落叶下",
        greeting="蜗牛慢慢探出触角，留下了一条安静的小路。",
    ),
]


ANIMAL_INTERACTIONS = {
    "observe": {"label": "观察", "friendship": 8, "xp": 5, "message": "你保持距离观察，伙伴更信任你了。"},
    "greet": {"label": "打招呼", "friendship": 10, "xp": 5, "message": "你轻轻打招呼，伙伴回应了你的陪伴。"},
    "care": {"label": "照顾伙伴", "friendship": 15, "xp": 8, "message": "你用今天的发现照顾伙伴，友好度提升了。"},
}


FOOD_EFFECTS = {
    "sun_nectar": {"hunger": 18, "mood": 10, "bond": 8, "xp": 35},
    "fresh_leaf": {"hunger": 15, "mood": 14, "bond": 8, "xp": 35},
    "shade_fruit": {"hunger": 22, "mood": 8, "bond": 8, "xp": 35},
}


def choose_plant(sequence: int, hint: str | None = None) -> Plant:
    if hint:
        lowered = hint.lower()
        for plant in PLANTS:
            if plant.key in lowered or plant.name in hint:
                return plant
    return PLANTS[sequence % len(PLANTS)]


def choose_animal(sequence: int) -> AnimalClue:
    return ANIMAL_CLUES[sequence % len(ANIMAL_CLUES)]


def animal_by_key(animal_key: str) -> AnimalClue | None:
    for animal in ANIMAL_CLUES:
        if animal.key == animal_key:
            return animal
    return None
