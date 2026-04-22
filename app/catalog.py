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
    ),
    AnimalClue(
        key="butterfly",
        name="蝴蝶线索",
        category="昆虫",
        rarity="common",
        knowledge="蝴蝶会在花朵附近吸食花蜜，也是植物传粉的帮手。",
        safety_tip="不要触碰翅膀，保持距离观察飞行路线。",
    ),
    AnimalClue(
        key="snail",
        name="蜗牛线索",
        category="软体动物",
        rarity="uncommon",
        knowledge="蜗牛喜欢潮湿环境，雨后更容易看到活动痕迹。",
        safety_tip="观察后不要带回家，也不要放到危险路面。",
    ),
]


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

