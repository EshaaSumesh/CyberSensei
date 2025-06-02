import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta

# Import CTF categories from your ctf.py
from ctf import CTF_CATEGORIES

def create_tables():
    try:
        connection = mysql.connector.connect(
            host='localhost',         # Replace with your MySQL host
            user='root',              # Replace with your MySQL username
            password='Chainsawman21'       # Replace with your MySQL password
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS ctf_data")
            cursor.execute("USE ctf_data")
            
            # Create users table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username VARCHAR(50) PRIMARY KEY,
                display_name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create challenges table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS challenges (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                category VARCHAR(50) NOT NULL,
                difficulty VARCHAR(20) NOT NULL,
                description TEXT NOT NULL,
                flag VARCHAR(255),
                points INT DEFAULT 0
            )
            ''')
            
            # Create user_logs table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(50) NOT NULL,
                challenge_id INT NOT NULL,
                category VARCHAR(50) NOT NULL,
                difficulty VARCHAR(20) NOT NULL,
                success TINYINT NOT NULL,
                attempts INT DEFAULT 1,
                time_taken INT DEFAULT 0,
                points INT DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (username),
                FOREIGN KEY (challenge_id) REFERENCES challenges (id)
            )
            ''')
            
            # Add some sample data for user "bob" if it doesn't exist
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'bob'")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO users (username, display_name) VALUES (%s, %s)", 
                              ('bob', 'Hackerman Bob'))
            
            # Add some sample challenges if none exist
            cursor.execute("SELECT COUNT(*) FROM challenges")
            if cursor.fetchone()[0] == 0:
                sample_challenges = [
                    ('SQL Injection Basics', 'Web Exploitation', 'Beginner', 'Find the flag using SQL injection', 'FLAG{sql_master}', 50),
                    ('Caesar\'s Secrets', 'Cryptography', 'Beginner', 'Decode the Caesar cipher', 'FLAG{hail_caesar}', 40),
                    ('Binary Analysis', 'Reverse Engineering', 'Intermediate', 'Analyze the binary to find the flag', 'FLAG{binary_master}', 70)
                ]
                
                for challenge in sample_challenges:
                    cursor.execute('''
                    INSERT INTO challenges (name, category, difficulty, description, flag, points) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ''', challenge)
            
            # Add some sample logs for bob if none exist
            cursor.execute("SELECT COUNT(*) FROM user_logs WHERE user_id = 'bob'")
            if cursor.fetchone()[0] == 0:
                # Get challenge IDs
                cursor.execute("SELECT id FROM challenges ORDER BY id LIMIT 3")
                challenge_ids = [row[0] for row in cursor.fetchall()]
                
                if challenge_ids:
                    sample_logs = [
                        ('bob', challenge_ids[0], 'Web Exploitation', 'Beginner', 1, 2, 340, 50),
                        ('bob', challenge_ids[1], 'Cryptography', 'Beginner', 1, 1, 180, 40),
                        ('bob', challenge_ids[2], 'Reverse Engineering', 'Intermediate', 0, 3, 720, 0)
                    ]
                    
                    for log in sample_logs:
                        cursor.execute('''
                        INSERT INTO user_logs (user_id, challenge_id, category, difficulty, success, attempts, time_taken, points) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ''', log)
            
            connection.commit()
            print("Tables created and sample data added successfully!")
            
    except Error as e:
        print(f"Error creating MySQL tables: {e}")
        
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

if __name__ == "__main__":
    create_tables() 