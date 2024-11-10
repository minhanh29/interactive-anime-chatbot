from typing import Union, List
from pydantic import BaseModel, Field


class Entity(BaseModel):
    id: int
    name: str
    relation: str
    related_person: Union[str, None] = None
    related_person_id: int = -1


class PlanningGenerationOutput(BaseModel):
    thinking: str
    refined_question: str
    need_attribute_dimension: bool
    topics: List[str]
    entities: List[Entity]
