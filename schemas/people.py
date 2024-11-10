from typing import Union, List, Optional
from pydantic import BaseModel, Field


class PeopleRow(BaseModel):
    attribute: str
    value: str
    content: str
    ref: Union[bool, None] = False
