from enum import Enum

from pydantic import BaseModel


class AlertRelabelOp(str, Enum):
    Add = "add"
    Replace = "replace"


class AlertRelabel(BaseModel):
    source: str
    target: str
    operation: AlertRelabelOp = AlertRelabelOp.Add
