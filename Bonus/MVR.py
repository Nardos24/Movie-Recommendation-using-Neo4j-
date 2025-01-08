import pandas as pd
from neo4j import GraphDatabase
import ast

#  Preprocess the Dataset

movies_df = pd.read_csv('movies_metadata.csv', low_memory=False)
ratings_df = pd.read_csv('ratings_small.csv')

movies_df = movies_df[['id', 'title', 'genres', 'release_date']]
movies_df = movies_df[movies_df['id'].str.isdigit()]
movies_df['id'] = movies_df['id'].astype(int)

def parse_genres(genres_str):
    genres = []
    try:
        genres_list = ast.literal_eval(genres_str)
        for genre in genres_list:
            genres.append(genre['name'])
    except:
        pass
    return genres

movies_df['genres_list'] = movies_df['genres'].apply(parse_genres)
movies_df['release_year'] = pd.to_datetime(movies_df['release_date'], errors='coerce').dt.year

ratings_df = ratings_df[ratings_df['movieId'].isin(movies_df['id'])]

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Nardi1234"))  # Replace 'your_password' with your Neo4j password

def create_constraints(tx):
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.userId IS UNIQUE;")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (m:Movie) REQUIRE m.id IS UNIQUE;")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE;")

with driver.session() as session:
    session.execute_write(create_constraints)

def add_movies_and_genres(tx, movies_batch):
    query = """
    UNWIND $movies AS movie
    MERGE (m:Movie {id: movie.id})
    SET m.title = movie.title, m.release_year = movie.release_year
    FOREACH (genreName IN movie.genres_list |
        MERGE (g:Genre {name: genreName})
        MERGE (m)-[:BELONGS_TO]->(g)
    )
    """
    tx.run(query, movies=movies_batch)

movies_data = movies_df[['id', 'title', 'release_year', 'genres_list']].to_dict('records')
batch_size = 1000
with driver.session() as session:
    for i in range(0, len(movies_data), batch_size):
        session.execute_write(add_movies_and_genres, movies_data[i:i+batch_size])

def add_users_and_ratings(tx, ratings_batch):
    query = """
    UNWIND $ratings AS rating
    MERGE (u:User {userId: rating.userId})
    MERGE (m:Movie {id: rating.movieId})
    MERGE (u)-[r:WATCHED]->(m)
    SET r.rating = rating.rating
    """
    tx.run(query, ratings=ratings_batch)

ratings_data = ratings_df[['userId', 'movieId', 'rating']].to_dict('records')
batch_size = 10000
with driver.session() as session:
    for i in range(0, len(ratings_data), batch_size):
        session.execute_write(add_users_and_ratings, ratings_data[i:i+batch_size])

def recommend_content_based(tx, user_id, limit=10):
    query = """
    MATCH (u:User {userId: $user_id})-[:WATCHED]->(m:Movie)-[:SIMILAR]->(rec:Movie)
    WHERE NOT (u)-[:WATCHED]->(rec)
    RETURN rec.title AS title, rec.release_year AS year
    LIMIT $limit
    """
    result = tx.run(query, user_id=user_id, limit=limit)
    return [record for record in result]

def recommend_collaborative(tx, user_id, limit=10):
    query = """
    MATCH (u1:User {userId: $user_id})-[:WATCHED]->(m:Movie)<-[:WATCHED]-(u2:User)
    MATCH (u2)-[:WATCHED]->(rec:Movie)
    WHERE NOT (u1)-[:WATCHED]->(rec)
    RETURN rec.title AS title, rec.release_year AS year
    LIMIT $limit
    """
    result = tx.run(query, user_id=user_id, limit=limit)
    return [record for record in result]

def recommend_movies(user_id):
    with driver.session() as session:
        recommendations = session.execute_read(recommend_content_based, user_id=user_id)
        if not recommendations:
            # Fallback to collaborative filtering
            recommendations = session.execute_read(recommend_collaborative, user_id=user_id)
        return recommendations

if __name__ == "__main__":
    # Create the movie-similarity graph in Neo4j
    with driver.session() as session:
        session.run("""
        CALL gds.graph.project(
          'movie-similarity-graph',
          'Movie',
          {BELONGS_TO: {type: 'BELONGS_TO', orientation: 'UNDIRECTED'}}
        )
        """)

        session.run("""
        CALL gds.nodeSimilarity.write('movie-similarity-graph', {
          similarityCutoff: 0.1,
          writeRelationshipType: 'SIMILAR',
          writeProperty: 'similarity'
        })
        """)

    # Get recommendations for a user
    user_id = 1
    recommendations = recommend_movies(user_id)

    if recommendations:
        print(f"Recommendations for User {user_id}:")
        for rec in recommendations:
            print(f"- {rec['title']} ({rec['year']})")
    else:
        print(f"No recommendations found for User {user_id}.")
    
    driver.close()
