from neo4j import GraphDatabase
import pandas as pd
import ast

# Connect to Neo4j
URI = "bolt://localhost:7687"  # Adjust if you're using a remote Neo4j instance
USERNAME = "neo4j"             # Your Neo4j username
PASSWORD = "Nardi1234"     # Your Neo4j password

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def execute_query(query, parameters=None):
    with driver.session() as session:
        session.run(query, parameters)

def preprocess_data():
    """
    Preprocess the data: Clean movies metadata and user ratings.
    """
    movies_df = pd.read_csv("movies_metadata.csv", low_memory=False)
    ratings_df = pd.read_csv("ratings_small.csv")

    # Clean movies data
    movies_df = movies_df[['id', 'title', 'genres', 'release_date']].dropna()
    movies_df['release_year'] = movies_df['release_date'].apply(lambda x: x.split('-')[0])

    # Parse genres correctly
    def extract_genres(genre_str):
        try:
            genre_list = ast.literal_eval(genre_str)  # Convert JSON-like string to Python list
            return [g['name'] for g in genre_list] if isinstance(genre_list, list) else []
        except Exception:
            return []

    movies_df['genres'] = movies_df['genres'].apply(extract_genres)

    # Clean ratings data
    ratings_df = ratings_df[['userId', 'movieId', 'rating']]

    return movies_df, ratings_df

def import_movies_and_genres(movies_df):
    """
    Import movies and genres into Neo4j.
    """
    for _, row in movies_df.iterrows():
        genres = row['genres']  # Extract genres

        # Create or match Movie nodes by unique 'id' property
        execute_query(
            """
            MERGE (m:Movie {id: $id})
            SET m.title = $title, m.release_year = $release_year
            """,
            {"id": row['id'], "title": row['title'], "release_year": row['release_year']}
        )

        # Create or match Genre nodes and link them to movies
        for genre in genres:
            execute_query(
                """
                MERGE (g:Genre {name: $genre})
                MERGE (m:Movie {id: $id})-[:BELONGS_TO]->(g)
                """,
                {"genre": genre, "id": row['id']}
            )

def import_ratings(ratings_df):
    """
    Import user ratings into Neo4j.
    """
    for _, row in ratings_df.iterrows():
        execute_query(
            """
            MERGE (u:User {id: $userId})
            MERGE (m:Movie {id: $movieId})
            MERGE (u)-[:WATCHED {rating: $rating}]->(m)
            """,
            {"userId": row['userId'], "movieId": row['movieId'], "rating": row['rating']}
        )

def generate_content_recommendations(user_id):
    """
    Generate content-based recommendations for a user.
    """
    query = """
    MATCH (u:User {id: $userId})-[:WATCHED]->(m:Movie)-[:SIMILAR]->(rec:Movie)
    RETURN rec.title AS recommendation
    LIMIT 10
    """
    with driver.session() as session:
        return [record['recommendation'] for record in session.run(query, {"userId": user_id})]

def generate_collaborative_recommendations(user_id):
    """
    Generate collaborative filtering recommendations for a user.
    """
    query = """
    MATCH (u:User {id: $userId})-[:SIMILAR_USER]->(similar:User)-[:WATCHED]->(rec:Movie)
    WHERE NOT (u)-[:WATCHED]->(rec)
    RETURN rec.title AS recommendation
    LIMIT 10
    """
    with driver.session() as session:
        return [record['recommendation'] for record in session.run(query, {"userId": user_id})]

if __name__ == "__main__":
    # Preprocess data
    movies_df, ratings_df = preprocess_data()
    print("Data preprocessed successfully.")

    # Import movies and genres
    import_movies_and_genres(movies_df)
    print("Movies and genres imported successfully.")

    # Import user ratings
    import_ratings(ratings_df)
    print("Ratings imported successfully.")

    # Generate recommendations
    user_id = 1  # Example user ID
    recommendations = generate_content_recommendations(user_id)
    if not recommendations:
        recommendations = generate_collaborative_recommendations(user_id)

    if not recommendations:
        recommendations = ["No recommendations available."]

    print(f"Recommended movies for user {user_id}: {recommendations}")
