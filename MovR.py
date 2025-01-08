from neo4j import GraphDatabase

# --- 1. Connect to Neo4j ---
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "nardi"))

# --- 2. Define Functions to Add Data ---
def add_movies_and_genres(tx, movies):
    query = """
    UNWIND $movies AS movie
    MERGE (m:Movie {id: movie.id, title: movie.title, release_year: movie.release_year})
    FOREACH (genre IN movie.genres |
        MERGE (g:Genre {name: genre})
        MERGE (m)-[:BELONGS_TO]->(g)
    )
    """
    tx.run(query, movies=movies)

def add_users_and_ratings(tx, ratings):
    query = """
    UNWIND $ratings AS rating
    MERGE (u:User {id: rating.user_id})
    MERGE (m:Movie {id: rating.movie_id})
    MERGE (u)-[:WATCHED {rating: rating.rating}]->(m)
    """
    tx.run(query, ratings=ratings)

# --- 3. Define Recommendation Query ---
def recommend_movies(tx, user_id):
    query = """
    MATCH (u:User {id: $user_id})-[:WATCHED]->(m:Movie)-[:BELONGS_TO]->(g:Genre)
    MATCH (rec:Movie)-[:BELONGS_TO]->(g)
    WHERE NOT (u)-[:WATCHED]->(rec)
    RETURN rec.title AS title, rec.release_year AS year
    LIMIT 5
    """
    result = tx.run(query, user_id=user_id)
    return [record for record in result]

# --- 4. Main Execution ---
if __name__ == "__main__":
    # Sample Data
    movies_data = [
    {"id": "1", "title": "Inception", "release_year": 2010, "genres": ["Sci-Fi", "Action"]},
    {"id": "2", "title": "Titanic", "release_year": 1997, "genres": ["Drama", "Romance"]},
    {"id": "3", "title": "The Matrix", "release_year": 1999, "genres": ["Sci-Fi", "Action"]},
    {"id": "4", "title": "Avatar", "release_year": 2009, "genres": ["Sci-Fi", "Adventure"]},
]

ratings_data = [
    {"user_id": "1", "movie_id": "1", "rating": 9},
    {"user_id": "1", "movie_id": "2", "rating": 8},
    {"user_id": "2", "movie_id": "1", "rating": 7},
    {"user_id": "2", "movie_id": "3", "rating": 8},
]


try:
        with driver.session() as session:
            # Add Movies and Genres
            print("Adding movies and genres...")
            session.execute_write(add_movies_and_genres, movies_data)

            # Add Users and Ratings
            print("Adding users and ratings...")
            session.execute_write(add_users_and_ratings, ratings_data)

            # Get Recommendations
            print("Getting recommendations for user 1...")
            recommendations = session.execute_read(recommend_movies, user_id="1")
            for movie in recommendations:
                print(f"Recommended: {movie['title']} ({movie['year']})")
finally:
        driver.close()
