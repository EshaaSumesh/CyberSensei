import mysql.connector
from mysql.connector import Error

class Database:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None
        self.connect()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.cursor = self.connection.cursor()
            print("Database connection successful.")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")

    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("Database connection closed.")

    def create_user(self, username, email):
        try:
            query = "INSERT INTO users (username, email) VALUES (%s, %s)"
            self.cursor.execute(query, (username, email))
            self.connection.commit()
            print(f"User {username} created successfully.")
        except Error as e:
            print(f"Error creating user: {e}")
    
    def log_attempt(self, user_id, challenge_id, status, score):
        try:
            query = """
            INSERT INTO attempts (user_id, challenge_id, status, score, attempt_time)
            VALUES (%s, %s, %s, %s, NOW())
            """
            self.cursor.execute(query, (user_id, challenge_id, status, score))
            self.connection.commit()
            print(f"Attempt logged successfully for user {user_id}.")
        except Error as e:
            print(f"Error logging attempt: {e}")

    def get_user_performance(self, user_id):
        try:
            query = """
            SELECT challenges.name, attempts.status, attempts.score, attempts.attempt_time
            FROM attempts
            JOIN challenges ON attempts.challenge_id = challenges.id
            WHERE attempts.user_id = %s
            ORDER BY attempts.attempt_time DESC
            """
            self.cursor.execute(query, (user_id,))
            results = self.cursor.fetchall()
            return results
        except Error as e:
            print(f"Error fetching user performance: {e}")
            return []

    def get_challenge_statistics(self, challenge_id):
        try:
            query = """
            SELECT COUNT(*) AS total_attempts, AVG(score) AS average_score
            FROM attempts
            WHERE challenge_id = %s
            """
            self.cursor.execute(query, (challenge_id,))
            result = self.cursor.fetchone()
            return result
        except Error as e:
            print(f"Error fetching challenge statistics: {e}")
            return None
