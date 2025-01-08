from neo4j import GraphDatabase
import pandas as pd
import ast

# Connect to Neo4j
URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "nardi1234"

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def execute_query(query, parameters=None):
    with driver.session() as session:
        session.run(query, parameters)

def preprocess_data():
    movies_df = pd.read_csv("movies_metadata.csv", low_memory=False)
    ratings_df = pd.read_csv("ratings_small.csv")

    # Clean movies data
    movies_df = movies_df[['id', 'title', 'genres', 'release_date']].dropna()
    movies_df['release_year'] = movies_df['release_date'].apply(lambda x: x.split('-')[0])
    movies_df['genres'] = movies_df['genres'].apply(
        lambda x: [g['name'] for g in ast.literal_eval(x)] if pd.notnull(x) and isinstance(x, str) else []
    )

    ratings_df = ratings_df[['userId', 'movieId', 'rating']]
    return movies_df, ratings_df

def import_movies_and_genres(movies_df):
    for _, row in movies_df.iterrows():
        genres = row['genres']
        execute_query(
            """
            MERGE (m:Movie {id: $id, title: $title, release_year: $release_year})
            """,
            {"id": row['id'], "title": row['title'], "release_year": row['release_year']}
        )
        for genre in genres:
            execute_query(
                """
                MERGE (g:Genre {name: $genre})
                MERGE (m)-[:BELONGS_TO]->(g)
                """,
                {"genre": genre}
            )

def import_ratings(ratings_df):
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
    query = """
    MATCH (u:User {id: $userId})-[:WATCHED]->(m:Movie)-[:SIMILAR]->(rec:Movie)
    RETURN rec.title AS recommendation
    LIMIT 10
    """
    with driver.session() as session:
        return [record['recommendation'] for record in session.run(query, {"userId": user_id})]

def generate_collaborative_recommendations(user_id):
    query = """
    MATCH (u:User {id: $userId})-[:SIMILAR_USER]->(similar:User)-[:WATCHED]->(rec:Movie)
    WHERE NOT (u)-[:WATCHED]->(rec)
    RETURN rec.title AS recommendation
    LIMIT 10
    """
    with driver.session() as session:
        return [record['recommendation'] for record in session.run(query, {"userId": user_id})]

if __name__ == "__main__":
    movies_df, ratings_df = preprocess_data()
    print("Data preprocessed successfully.")

    import_movies_and_genres(movies_df)
    import_ratings(ratings_df)
    print("Data imported into Neo4j.")

    user_id = 1
    recommendations = generate_content_recommendations(user_id)
    if not recommendations:
        recommendations = generate_collaborative_recommendations(user_id)

    if not recommendations:
        recommendations = ["No recommendations available."]

    print(f"Recommended movies for user {user_id}: {recommendations}")
