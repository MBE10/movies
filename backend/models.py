from pydantic import BaseModel
from typing import Optional

class MovieCreate(BaseModel):
    title: str
    director: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    rating: Optional[float] = None
    description: Optional[str] = None

class MovieUpdate(BaseModel):
    title: Optional[str] = None
    director: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    rating: Optional[float] = None
    description: Optional[str] = None

class Movie(BaseModel):
    id: int
    title: str
    director: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    rating: Optional[float] = None
    description: Optional[str] = None
    user_id: int
