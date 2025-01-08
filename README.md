adjustments:

markdown

Copy
# Movie Recommendation System

This project demonstrates a Movie Recommendation System using a Neo4j graph database and Python. The system utilizes both content-based filtering and collaborative filtering techniques to recommend movies to users based on their viewing history and preferences. Below is a graphical representation of the data model used in this project.

## Data Model

The graph database consists of the following components:

### Nodes

- **User**: Represents users who interact with the system. Example users include Feven, Abebe, Chaltu, Smarawit, and Chala.
  
- **Movie**: Represents movies with attributes like title, genre, release_year, and rating. Examples include Inception, The Matrix, and Interstellar.
  
- **Genre**: Represents the genre categories for movies, such as Action, Comedy, Drama, and Sci-Fi.

### Relationships

- **WATCHED**: Connects a User to a Movie they have watched. Includes the user's rating for the movie.

- **BELONGS_TO**: Connects a Movie to a Genre.

## Features

### Content-Based Filtering

Recommends movies based on the genres of movies a user has previously watched. For example, if a user enjoys Sci-Fi movies, the system suggests other Sci-Fi movies they haven't watched yet.

### Collaborative Filtering

Recommends movies based on the viewing history of similar users. For example, if two users have overlapping movie preferences, the system recommends movies watched by one user to the other.

### Neo4j Graph Representation

The graph database visualized above shows:

- Users connected to the movies they have watched (WATCHED).
- Movies connected to their respective genres (BELONGS_TO).

**Example**: Feven has watched Interstellar and The Shawshank Redemption, which belong to the genres Sci-Fi and Drama, respectively.

## Installation and Setup

### Prerequisites

- Python 3.8+
- Neo4j (Community or Enterprise Edition)
- Neo4j Python Driver (`neo4j`)

### Steps

1. **Clone this repository**:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
Install dependencies:
```bash
pip install neo4j
 ```
## Set up  Neo4j database:
Start the Neo4j database server.
Import the provided data model using the Cypher scripts in the scripts folder.
Update database connection credentials in the Python script:

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "password"
Run the recommendation system:

python recommend.py
## Example Queries
List All Movies:
 ```cypher
MATCH (m:Movie)
RETURN m.title AS Title, m.genre AS Genre, m.release_year AS ReleaseYear, m.rating AS Rating;
 ```
## List All Users:
```cypher
MATCH (u:User)
RETURN u.name AS Name;
```
## Get Movies Watched by a Specific User:
```cypher

MATCH (u:User {name: 'Feven'})-[:WATCHED]->(m:Movie)
RETURN m.title AS WatchedMovies;
```
## Find Recommendations for a User (Collaborative Filtering):

```cypher
MATCH (u1:User {name: 'Feven'})-[:WATCHED]->(m:Movie)
MATCH (u2:User)-[:WATCHED]->(m)
WHERE u1 <> u2
MATCH (u2)-[:WATCHED]->(rec:Movie)
WHERE NOT (u1)-[:WATCHED]->(rec)
RETURN rec.title AS RecommendedMovies;
```



