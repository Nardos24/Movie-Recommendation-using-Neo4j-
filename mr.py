from neo4j import GraphDatabase

class MovieRecommendationSystem:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def recommend_movies(self, username):
        with self.driver.session() as session:
            content_based = session.execute_read(self._content_based_recommendations, username)
            collaborative = session.execute_read(self._collaborative_filtering_recommendations, username)

            return {
                "Content-Based Recommendations": content_based,
                "Collaborative Filtering Recommendations": collaborative
            }

    @staticmethod
    def _content_based_recommendations(tx, username):
        query = """
        MATCH (u:User {name: $username})-[:WATCHED]->(m:Movie)-[:BELONGS_TO]->(g:Genre)<-[:BELONGS_TO]-(rec:Movie)
        WHERE NOT (u)-[:WATCHED]->(rec)
        RETURN DISTINCT rec.title AS title, rec.genre AS genre, rec.release_year AS release_year, rec.rating AS rating
        ORDER BY rec.rating DESC LIMIT 10
        """
        result = tx.run(query, username=username)
        return [record.data() for record in result]

    @staticmethod
    def _collaborative_filtering_recommendations(tx, username):
        query = """
        MATCH (u1:User {name: $username})-[:WATCHED]->(m:Movie)
        MATCH (u2:User)-[:WATCHED]->(m)
        WHERE u1 <> u2
        MATCH (u2)-[:WATCHED]->(rec:Movie)
        WHERE NOT (u1)-[:WATCHED]->(rec)
        AND NOT EXISTS {
            MATCH (u1:User {name: $username})-[:WATCHED]->(cm:Movie)-[:BELONGS_TO]->(g:Genre)<-[:BELONGS_TO]-(rec)
        }
        RETURN rec.title AS title, rec.genre AS genre, rec.release_year AS release_year, rec.rating AS rating,
               COUNT(*) AS shared_interests
        ORDER BY shared_interests DESC, rec.rating DESC LIMIT 10
        """
        result = tx.run(query, username=username)
        return [record.data() for record in result]

if __name__ == "__main__":
  
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "jesusizma1" 
    
    recommender = MovieRecommendationSystem(URI, USER, PASSWORD)

    
    username = "Kebede"
    recommendations = recommender.recommend_movies(username)

  
    print("Recommendations for", username)
    print("\nContent-Based Recommendations:")
    for movie in recommendations["Content-Based Recommendations"]:
        print(f"- {movie['title']} ({movie['genre']}, {movie['release_year']}, Rating: {movie['rating']})")

    print("\nCollaborative Filtering Recommendations:")
    for movie in recommendations["Collaborative Filtering Recommendations"]:
        print(f"- {movie['title']} ({movie['genre']}, {movie['release_year']}, Rating: {movie['rating']})")

    recommender.close()
