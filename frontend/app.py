import streamlit as st
import requests
from typing import Optional

API_URL = "http://localhost:8000/api"

st.set_page_config(page_title="Movie Manager", layout="wide")

def init_session_state():
    if "token" not in st.session_state:
        st.session_state.token = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "movies" not in st.session_state:
        st.session_state.movies = []

def login(username: str, password: str) -> Optional[str]:
    try:
        response = requests.post(
            f"{API_URL}/login",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return None

def register(username: str, password: str) -> bool:
    try:
        response = requests.post(
            f"{API_URL}/register",
            json={"username": username, "password": password},
            timeout=5
        )

        if response.status_code in (200, 201):
            return True

        elif response.status_code == 400:
            st.error("Username already exists")

        else:
            st.error(f"Register failed: {response.text}")

        return False

    except Exception as e:
        st.error(f"Registration error: {str(e)}")
        return False


def get_movies(token: str):
    try:
        response = requests.get(
            f"{API_URL}/movies",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching movies: {str(e)}")
        return []

def create_movie(token: str, movie_data: dict):
    try:
        response = requests.post(
            f"{API_URL}/movies",
            json=movie_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.status_code == 201
    except Exception as e:
        st.error(f"Error creating movie: {str(e)}")
        return False

def update_movie(token: str, movie_id: int, movie_data: dict):
    try:
        response = requests.put(
            f"{API_URL}/movies/{movie_id}",
            json=movie_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error updating movie: {str(e)}")
        return False

def delete_movie(token: str, movie_id: int):
    try:
        response = requests.delete(
            f"{API_URL}/movies/{movie_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.status_code == 204
    except Exception as e:
        st.error(f"Error deleting movie: {str(e)}")
        return False

def show_login_page():
    st.title("Movie Manager")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", type="primary"):
            if username and password:
                token = login(username, password)
                if token:
                    st.session_state.token = token
                    st.session_state.username = username
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter username and password")

    with tab2:
        st.subheader("Register")
        reg_username = st.text_input("Username", key="reg_username")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_password_confirm = st.text_input("Confirm Password", type="password", key="reg_password_confirm")

        if st.button("Register", type="primary"):
            if reg_username and reg_password and reg_password_confirm:
                if reg_password != reg_password_confirm:
                    st.error("Passwords do not match")
                elif len(reg_password) < 4:
                    st.error("Password must be at least 4 characters")
                else:
                    token = register(reg_username, reg_password)
                    if token:
                        st.session_state.token = token
                        st.session_state.username = reg_username
                        st.success("Registered successfully!")
                        st.rerun()
            else:
                st.warning("Please fill in all fields")

def show_movie_manager():
    st.title("Movie Manager")

    with st.sidebar:
        st.header(f"Welcome, {st.session_state.username}!")

        if st.button("Logout", type="primary"):
            st.session_state.token = None
            st.session_state.username = None
            st.session_state.movies = []
            st.rerun()

        st.divider()

        st.subheader("Add New Movie")

        with st.form("add_movie_form"):
            title = st.text_input("Title*")
            director = st.text_input("Director")
            year = st.number_input("Year", min_value=1800, max_value=2100, value=2024, step=1)
            genre = st.selectbox("Genre", ["Action", "Comedy", "Drama", "Horror", "Sci-Fi", "Thriller", "Romance", "Documentary", "Other"])
            rating = st.slider("Rating", 0.0, 10.0, 5.0, 0.1)
            description = st.text_area("Description")

            submitted = st.form_submit_button("Add Movie", type="primary")

            if submitted:
                if not title:
                    st.error("Title is required")
                else:
                    movie_data = {
                        "title": title,
                        "director": director if director else None,
                        "year": int(year),
                        "genre": genre,
                        "rating": float(rating),
                        "description": description if description else None
                    }

                    if create_movie(st.session_state.token, movie_data):
                        st.success("Movie added successfully!")
                        st.rerun()

    movies = get_movies(st.session_state.token)

    if not movies:
        st.info("No movies found. Add your first movie using the sidebar!")
    else:
        st.subheader(f"Your Movies ({len(movies)})")

        cols = st.columns(3)

        for idx, movie in enumerate(movies):
            with cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"### {movie['title']}")

                    if movie.get('director'):
                        st.write(f"**Director:** {movie['director']}")

                    if movie.get('year'):
                        st.write(f"**Year:** {movie['year']}")

                    if movie.get('genre'):
                        st.write(f"**Genre:** {movie['genre']}")

                    if movie.get('rating'):
                        st.write(f"**Rating:** {movie['rating']}/10")

                    if movie.get('description'):
                        with st.expander("Description"):
                            st.write(movie['description'])

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("Edit", key=f"edit_{movie['id']}", use_container_width=True):
                            st.session_state.editing_movie = movie
                            st.rerun()

                    with col2:
                        if st.button("Delete", key=f"delete_{movie['id']}", type="secondary", use_container_width=True):
                            if delete_movie(st.session_state.token, movie['id']):
                                st.success("Movie deleted!")
                                st.rerun()

    if "editing_movie" in st.session_state:
        movie = st.session_state.editing_movie
        with st.expander(f"Edit Movie: {movie['title']}", expanded=True):
            with st.form("edit_movie_form"):
                title = st.text_input("Title*", value=movie['title'])
                director = st.text_input("Director", value=movie.get('director', ''))
                year = st.number_input("Year", min_value=1800, max_value=2100, value=movie.get('year', 2024), step=1)
                genre = st.selectbox(
                    "Genre",
                    ["Action", "Comedy", "Drama", "Horror", "Sci-Fi", "Thriller", "Romance", "Documentary", "Other"],
                    index=["Action", "Comedy", "Drama", "Horror", "Sci-Fi", "Thriller", "Romance", "Documentary", "Other"].index(movie.get('genre', 'Other'))
                )
                rating = st.slider("Rating", 0.0, 10.0, float(movie.get('rating', 5.0)), 0.1)
                description = st.text_area("Description", value=movie.get('description', ''))

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Update", use_container_width=True):
                        if not title:
                            st.error("Title is required")
                        else:
                            movie_data = {
                                "title": title,
                                "director": director or None,
                                "year": int(year),
                                "genre": genre,
                                "rating": float(rating),
                                "description": description or None
                            }
                            if update_movie(st.session_state.token, movie['id'], movie_data):
                                st.success("Movie updated!")
                                del st.session_state.editing_movie
                                st.rerun()
                with col2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        del st.session_state.editing_movie
                        st.rerun()



def main():
    init_session_state()

    if st.session_state.token:
        show_movie_manager()
    else:
        show_login_page()

if __name__ == "__main__":
    main()
