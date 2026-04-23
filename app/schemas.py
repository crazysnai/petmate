from __future__ import annotations

from pydantic import BaseModel, Field


class ChildCreate(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    age: int = Field(ge=6, le=12)
    guardian_name: str = Field(min_length=1, max_length=32)


class PetCreate(BaseModel):
    child_id: int
    name: str = Field(min_length=1, max_length=32)


class WalkReport(BaseModel):
    child_id: int
    distance_delta_meters: int = Field(gt=0, le=3000)
    steps_delta: int | None = Field(default=None, ge=0, le=10000)
    active_minutes_delta: int | None = Field(default=None, ge=0, le=240)


class PlantScan(BaseModel):
    child_id: int
    image_name: str | None = None


class AnimalClueDiscover(BaseModel):
    child_id: int


class FeedPet(BaseModel):
    child_id: int
    food_key: str


class GuardianSettingsUpdate(BaseModel):
    child_id: int
    outdoor_enabled: bool = True
    animal_clues_enabled: bool = True
    friends_enabled: bool = False
    garden_help_enabled: bool = True
    garden_likes_enabled: bool = True
    daily_distance_goal: int = Field(default=500, ge=100, le=3000)
    max_daily_distance: int = Field(default=3000, ge=500, le=10000)
    sleep_start: str = Field(default="21:00", pattern=r"^\d{2}:\d{2}$")
    sleep_end: str = Field(default="07:00", pattern=r"^\d{2}:\d{2}$")
    study_mode_enabled: bool = True
    study_start: str = Field(default="08:00", pattern=r"^\d{2}:\d{2}$")
    study_end: str = Field(default="17:00", pattern=r"^\d{2}:\d{2}$")


class AnimalInteract(BaseModel):
    child_id: int
    animal_key: str = Field(min_length=1, max_length=32)
    action: str = Field(pattern="^(observe|greet|share_food|play|mini_adventure|decorate_home)$")
