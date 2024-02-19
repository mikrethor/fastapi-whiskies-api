from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, *args, **kwargs):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, *args, **kwargs):
        field_schema.update(type="string")


class Whisky(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias='_id')
    bottle: str = Field(..., alias="bottle")
    price: str = Field(..., alias="price")
    rating: str = Field(..., alias="rating")
    region: str = Field(..., alias="region")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "bottle": "Lagavulin 16",
                "price": "99.99",
                "rating": "9.5",
                "region": "Islay"
            }
        }
