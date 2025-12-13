from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
from typing import List
import sqlite3

from database import get_db, init_db
from auth import (
    verify_password, get_password_hash, create_access_token,
    decode_access_token, Token, User, UserCreate, ACCESS_TOKEN_EXPIRE_MINUTES
)
from models import Movie, MovieCreate, MovieUpdate

app = FastAPI(title="Movies API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

init_db()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token = credentials.credentials
    token_data = decode_access_token(token)
    if token_data is None or token_data.username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE username = ?", (token_data.username,))
    user_row = cursor.fetchone()
    conn.close()

    if user_row is None:
        raise HTTPException(status_code=404, detail="User not found")

    return User(id=user_row["id"], username=user_row["username"])

@app.post("/api/register", response_model=Token)
def register(user: UserCreate):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (user.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user.password)
    cursor.execute(
        "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
        (user.username, hashed_password)
    )
    conn.commit()
    conn.close()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/login", response_model=Token)
def login(user: UserCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT hashed_password FROM users WHERE username = ?", (user.username,))
    user_row = cursor.fetchone()
    conn.close()

    if not user_row or not verify_password(user.password, user_row["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/movies", response_model=List[Movie])
def get_movies(current_user: User = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, director, year, genre, rating, description, user_id FROM movies WHERE user_id = ?",
        (current_user.id,)
    )
    movies = cursor.fetchall()
    conn.close()

    return [dict(movie) for movie in movies]

@app.post("/api/movies", response_model=Movie, status_code=status.HTTP_201_CREATED)
def create_movie(movie: MovieCreate, current_user: User = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO movies (title, director, year, genre, rating, description, user_id)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (movie.title, movie.director, movie.year, movie.genre, movie.rating, movie.description, current_user.id)
    )
    conn.commit()
    movie_id = cursor.lastrowid
    conn.close()

    return {
        "id": movie_id,
        "title": movie.title,
        "director": movie.director,
        "year": movie.year,
        "genre": movie.genre,
        "rating": movie.rating,
        "description": movie.description,
        "user_id": current_user.id
    }

@app.get("/api/movies/{movie_id}", response_model=Movie)
def get_movie(movie_id: int, current_user: User = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, director, year, genre, rating, description, user_id FROM movies WHERE id = ? AND user_id = ?",
        (movie_id, current_user.id)
    )
    movie = cursor.fetchone()
    conn.close()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    return dict(movie)

@app.put("/api/movies/{movie_id}", response_model=Movie)
def update_movie(movie_id: int, movie_update: MovieUpdate, current_user: User = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM movies WHERE id = ? AND user_id = ?", (movie_id, current_user.id))
    existing_movie = cursor.fetchone()

    if not existing_movie:
        conn.close()
        raise HTTPException(status_code=404, detail="Movie not found")

    update_data = movie_update.model_dump(exclude_unset=True)

    if update_data:
        set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
        values = list(update_data.values()) + [movie_id, current_user.id]
        cursor.execute(
            f"UPDATE movies SET {set_clause} WHERE id = ? AND user_id = ?",
            values
        )
        conn.commit()

    cursor.execute(
        "SELECT id, title, director, year, genre, rating, description, user_id FROM movies WHERE id = ?",
        (movie_id,)
    )
    updated_movie = cursor.fetchone()
    conn.close()

    return dict(updated_movie)

@app.delete("/api/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int, current_user: User = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM movies WHERE id = ? AND user_id = ?", (movie_id, current_user.id))

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Movie not found")

    conn.commit()
    conn.close()

    return None

@app.get("/")
def root():
    return {"message": "Movies API is running"}
