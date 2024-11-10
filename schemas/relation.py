from typing import Union, List, Optional
from pydantic import BaseModel, Field


class RelationItem(BaseModel):
    relation: Union[str, None] = "none"
    value: Union[str, None] = "none"
    related_database: Union[list, str] = []


class RelationGenerationOutput(BaseModel):
    refined_question: str
    relations: List[RelationItem]
