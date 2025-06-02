from flask import Flask, jsonify, request
from flask_cors import CORS
import random
from datetime import datetime
import mysql.connector
import traceback
import sys
import os

# Import the CTF model
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ctf import CTFChallengeModel

app = Flask(__name__)
CORS(app)

SECRET_PREFIX = "CTF{"

# Initialize the CTF challenge model
ctf_model = CTFChallengeModel()

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Chainsawman21",
    "database": "ctf_data"
}

# Connect to database
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("✅ Database connection successful")
        return conn
    except Exception as e:
        print(f"⚠️ Database connection error: {e}")
        traceback.print_exc()
        return None

# Achievement definitions
ACHIEVEMENT_DEFINITIONS = [
    {
        "id": "first_challenge",
        "name": "Getting Started",
        "description": "Complete your first challenge",
        "icon": "🚀",
        "points": 10,
        "condition": lambda stats: stats["challenges_completed"] >= 1
    },
    {
        "id": "speed_demon",
        "name": "Speed Demon",
        "description": "Solve a challenge in under 60 seconds",
        "icon": "⚡",
        "points": 20,
        "condition": lambda stats: stats["fastest_solve"] is not None and stats["fastest_solve"] < 60
    },
    {
        "id": "hard_solver",
        "name": "Hard Hitter",
        "description": "Complete a Hard challenge",
        "icon": "🔥",
        "points": 30,
        "condition": lambda stats: stats["difficulty_count"].get("Hard", 0) >= 1
    },
    {
        "id": "perfect_solve",
        "name": "Perfect Solver",
        "description": "Solve a challenge with no wrong attempts",
        "icon": "✨",
        "points": 15,
        "condition": lambda stats: stats["perfect_solves"] >= 1
    },
    {
        "id": "categories_explorer",
        "name": "Explorer",
        "description": "Complete challenges from at least 3 different categories",
        "icon": "🧭",
        "points": 25,
        "condition": lambda stats: len(stats["category_count"]) >= 3
    }
]

# Initialize database tables
def init_db():
    """Initialize the MySQL database tables if they don't exist."""
    conn = get_db_connection()
    if not conn:
        print("⚠️ Skipping database initialization - no connection")
        return
        
    try:
        cursor = conn.cursor()
        
        # User Attempts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_attempts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255),
                category VARCHAR(255),
                challenge TEXT,
                user_answer TEXT,
                attempts INT,
                time_taken FLOAT,
                completed BOOLEAN,
                points INT,
                difficulty VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User Profile table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id VARCHAR(255) PRIMARY KEY,
                total_points INT DEFAULT 0,
                challenges_completed INT DEFAULT 0,
                fastest_solve FLOAT DEFAULT NULL
            )
        ''')
        
        # User Achievements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255),
                achievement_id VARCHAR(255),
                achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, achievement_id)
            )
        ''')
        
        # Leaderboard table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaderboard (
                user_id VARCHAR(255) PRIMARY KEY,
                username VARCHAR(255),
                total_points INT DEFAULT 0,
                challenges_completed INT DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Error initializing database: {e}")
        traceback.print_exc()
    finally:
        if conn:
            cursor.close()
            conn.close()

# Initialize the database on startup
init_db()

# Calculate points based on difficulty and attempts
def calculate_points(difficulty, attempts, time_taken=None):
    base_points = {"Easy": 10, "Medium": 25, "Hard": 50}
    
    # Base points from difficulty
    points = base_points.get(difficulty, 10)
    
    # Deduct points for multiple attempts (but never below 30% of base)
    if attempts > 1:
        points = max(points * (1 - 0.2 * (attempts - 1)), points * 0.3)
    
    # Bonus for fast solves
    if time_taken and time_taken < 60:  # Less than 1 minute
        points += points * 0.2  # 20% bonus
    
    return int(points)

# Check and award achievements
def check_achievements(username):
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get user's stats for achievement checking
        user_stats = get_user_stats(username)
        if not user_stats:
            return []
            
        # Get already achieved achievements
        cursor.execute('SELECT achievement_id FROM user_achievements WHERE user_id = %s', (username,))
        existing_achievements = [row['achievement_id'] for row in cursor.fetchall()]
        
        new_achievements = []
        
        for achievement in ACHIEVEMENT_DEFINITIONS:
            # Skip if already earned
            if achievement["id"] in existing_achievements:
                continue
            
            # Check if condition is met
            if achievement["condition"](user_stats):
                # Add achievement to database
                cursor.execute('''
                    INSERT INTO user_achievements (user_id, achievement_id)
                    VALUES (%s, %s)
                ''', (username, achievement["id"]))
                
                # Update user's total points
                cursor.execute('''
                    UPDATE user_profiles 
                    SET total_points = total_points + %s 
                    WHERE user_id = %s
                ''', (achievement["points"], username))
                
                # Update leaderboard
                cursor.execute('''
                    UPDATE leaderboard 
                    SET total_points = total_points + %s 
                    WHERE user_id = %s
                ''', (achievement["points"], username))
                
                new_achievements.append({
                    "id": achievement["id"],
                    "name": achievement["name"],
                    "description": achievement["description"],
                    "icon": achievement["icon"],
                    "points": achievement["points"]
                })
        
        conn.commit()
        return new_achievements
    except Exception as e:
        print(f"❌ Error checking achievements: {e}")
        traceback.print_exc()
        return []
    finally:
        if conn:
            cursor.close()
            conn.close()

# Calculate user stats
def get_user_stats(username):
    print(f"✅ Fetching stats for user: {username}")
    
    try:
        conn = get_db_connection()
        if not conn:
            print("⚠️ Database connection failed in get_user_stats")
            return None
        
        cursor = conn.cursor(dictionary=True)
        
        # Get basic user profile
        cursor.execute('SELECT * FROM user_profiles WHERE user_id = %s', (username,))
        profile = cursor.fetchone()
        
        if not profile:
            print(f"⚠️ No profile found for user: {username}")
            # User doesn't exist yet - return empty stats
            empty_stats = {
                "challenges_attempted": 0,
                "challenges_completed": 0,
                "total_points": 0,
                "fastest_solve": None,
                "perfect_solves": 0,
                "category_count": {},
                "difficulty_count": {},
                "achievements": [],
                "recent_activity": []
            }
            return empty_stats
            
        # Start building stats dict - ensure proper type conversion
        stats = {
            "challenges_attempted": 0,
            "challenges_completed": int(profile['challenges_completed']),
            "total_points": int(profile['total_points']),
            "fastest_solve": float(profile['fastest_solve']) if profile['fastest_solve'] is not None else None,
            "perfect_solves": 0,
            "category_count": {},
            "difficulty_count": {}
        }
        
        # Get attempts data
        cursor.execute('''
            SELECT category, difficulty, completed, attempts
            FROM user_attempts 
            WHERE user_id = %s
        ''', (username,))
        attempts = cursor.fetchall()
        
        # Count attempts and categorize
        stats["challenges_attempted"] = len(attempts)
        
        for attempt in attempts:
            if attempt['completed']:
                # Count by category
                category = attempt['category']
                if category in stats["category_count"]:
                    stats["category_count"][category] += 1
                else:
                    stats["category_count"][category] = 1
                    
                # Count by difficulty
                difficulty = attempt['difficulty']
                if difficulty in stats["difficulty_count"]:
                    stats["difficulty_count"][difficulty] += 1
                else:
                    stats["difficulty_count"][difficulty] = 1
                
                # Perfect solves (solved in 1 attempt)
                if attempt['attempts'] == 1:
                    stats["perfect_solves"] += 1
        
        # Get user achievements
        cursor.execute('''
            SELECT achievement_id 
            FROM user_achievements 
            WHERE user_id = %s
        ''', (username,))
        
        achievement_ids = [row['achievement_id'] for row in cursor.fetchall()]
        achievements = [
            {
                "id": aid,
                "name": next((a["name"] for a in ACHIEVEMENT_DEFINITIONS if a["id"] == aid), "Unknown"),
                "description": next((a["description"] for a in ACHIEVEMENT_DEFINITIONS if a["id"] == aid), ""),
                "icon": next((a["icon"] for a in ACHIEVEMENT_DEFINITIONS if a["id"] == aid), "🏆")
            }
            for aid in achievement_ids
        ]
        
        stats["achievements"] = achievements
        
        # Get recent activity
        cursor.execute('''
            SELECT 
                challenge, category, difficulty, completed, attempts, 
                UNIX_TIMESTAMP(timestamp) as timestamp_unix
            FROM user_attempts
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT 5
        ''', (username,))
        
        recent_activity = cursor.fetchall()
        
        # Convert MySQL objects to Python/JSON-serializable types
        formatted_activity = []
        for activity in recent_activity:
            formatted_activity.append({
                "challenge": activity['challenge'],
                "category": activity['category'],
                "difficulty": activity['difficulty'],
                "completed": bool(activity['completed']),
                "attempts": int(activity['attempts']),
                "timestamp": int(activity['timestamp_unix']) if activity['timestamp_unix'] else 0
            })
        
        stats["recent_activity"] = formatted_activity
        
        cursor.close()
        conn.close()
        
        print(f"✅ Successfully fetched stats for user: {username}")
        return stats
        
    except Exception as e:
        print(f"❌ Error getting user stats: {e}")
        traceback.print_exc()
        
        # Return empty stats instead of error
        empty_stats = {
            "challenges_attempted": 0,
            "challenges_completed": 0,
            "total_points": 0,
            "fastest_solve": None,
            "perfect_solves": 0,
            "category_count": {},
            "difficulty_count": {},
            "achievements": [],
            "recent_activity": []
        }
        return empty_stats

# Route to submit answers and track progress
@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    username = data.get('username')
    
    if not username:
        return jsonify({"error": "Username is required"}), 400
        
    challenge_id = data.get('challenge', '')
    category = data.get('category', 'Unknown')
    difficulty = data.get('difficulty', 'Unknown')
    attempts = data.get('attempts', 1)
    start_time = data.get('start_time')
    user_answer = data.get('user_answer', '')
    result = data.get('result', '')
    
    # Calculate time taken if start_time is provided
    time_taken = None
    if start_time:
        time_taken = (datetime.now().timestamp() - start_time)
    
    # Determine if challenge is completed
    completed = True if "Correct" in result else False
    
    # Calculate points for completed challenges
    points_earned = 0
    if completed:
        points_earned = calculate_points(difficulty, attempts, time_taken)
    
    conn = get_db_connection()
    if not conn:
        return jsonify({
            "success": False,
            "error": "Database connection failed"
        }), 500
        
    try:
        cursor = conn.cursor()
        
        # Store the attempt in user_attempts table
        cursor.execute('''
            INSERT INTO user_attempts (
                user_id, category, challenge, user_answer, 
                attempts, time_taken, completed, points, difficulty, timestamp
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ''', (
            username, category, challenge_id, user_answer, 
            attempts, time_taken, completed, points_earned, difficulty
        ))
        
        # Update user_profiles table or create if not exists
        cursor.execute('''
            INSERT INTO user_profiles (user_id, total_points, challenges_completed, fastest_solve)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                total_points = total_points + %s,
                challenges_completed = challenges_completed + %s,
                fastest_solve = CASE 
                    WHEN fastest_solve IS NULL OR %s < fastest_solve THEN %s 
                    ELSE fastest_solve 
                END
        ''', (
            username, 
            points_earned if completed else 0, 
            1 if completed else 0,
            time_taken if completed else None,
            points_earned if completed else 0,
            1 if completed else 0,
            time_taken if completed and time_taken else 0,
            time_taken if completed and time_taken else 0
        ))
        
        # Update leaderboard table
        cursor.execute('''
            INSERT INTO leaderboard (user_id, username, total_points, challenges_completed)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                username = %s,
                total_points = total_points + %s,
                challenges_completed = challenges_completed + %s
        ''', (
            username, 
            username, 
            points_earned if completed else 0, 
            1 if completed else 0,
            username,
            points_earned if completed else 0,
            1 if completed else 0
        ))
        
        conn.commit()
        
        # Check for new achievements if challenge completed
        new_achievements = []
        if completed:
            new_achievements = check_achievements(username)
        
        return jsonify({
            "success": True,
            "points": points_earned,
            "achievements": new_achievements
        })
        
    except Exception as e:
        print(f"❌ Error submitting answer: {e}")
        traceback.print_exc()
        
        if conn:
            conn.rollback()
            
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

# Get user stats
@app.route('/user_stats/<username>', methods=['GET'])
def user_stats(username):
    print(f"✅ Fetching stats for user: {username}")
    
    try:
        conn = get_db_connection()
        if not conn:
            print("⚠️ Database connection failed in user_stats route")
            # Return empty stats instead of error
            empty_stats = {
                "challenges_attempted": 0,
                "challenges_completed": 0,
                "total_points": 0,
                "fastest_solve": None,
                "perfect_solves": 0,
                "category_count": {},
                "difficulty_count": {},
                "achievements": [],
                "recent_activity": []
            }
            return jsonify(empty_stats)
            
        cursor = conn.cursor(dictionary=True)
        
        # Get basic user profile
        cursor.execute('SELECT * FROM user_profiles WHERE user_id = %s', (username,))
        profile = cursor.fetchone()
        
        if not profile:
            print(f"⚠️ No profile found for user: {username}")
            # User doesn't exist yet - return empty stats
            empty_stats = {
                "challenges_attempted": 0,
                "challenges_completed": 0,
                "total_points": 0,
                "fastest_solve": None,
                "perfect_solves": 0,
                "category_count": {},
                "difficulty_count": {},
                "achievements": [],
                "recent_activity": []
            }
            return jsonify(empty_stats)
            
        # Start building stats dict - ensure proper type conversion
        stats = {
            "challenges_attempted": 0,
            "challenges_completed": int(profile['challenges_completed']),
            "total_points": int(profile['total_points']),
            "fastest_solve": float(profile['fastest_solve']) if profile['fastest_solve'] is not None else None,
            "perfect_solves": 0,
            "category_count": {},
            "difficulty_count": {}
        }
        
        # Get attempts data
        cursor.execute('''
            SELECT category, difficulty, completed, attempts
            FROM user_attempts 
            WHERE user_id = %s
        ''', (username,))
        attempts = cursor.fetchall()
        
        # Count attempts and categorize
        stats["challenges_attempted"] = len(attempts)
        
        for attempt in attempts:
            if attempt['completed']:
                # Count by category
                category = attempt['category']
                if category in stats["category_count"]:
                    stats["category_count"][category] += 1
                else:
                    stats["category_count"][category] = 1
                    
                # Count by difficulty
                difficulty = attempt['difficulty']
                if difficulty in stats["difficulty_count"]:
                    stats["difficulty_count"][difficulty] += 1
                else:
                    stats["difficulty_count"][difficulty] = 1
                
                # Perfect solves (solved in 1 attempt)
                if attempt['attempts'] == 1:
                    stats["perfect_solves"] += 1
        
        # Get user achievements
        cursor.execute('''
            SELECT achievement_id 
            FROM user_achievements 
            WHERE user_id = %s
        ''', (username,))
        
        achievement_ids = [row['achievement_id'] for row in cursor.fetchall()]
        achievements = [
            {
                "id": aid,
                "name": next((a["name"] for a in ACHIEVEMENT_DEFINITIONS if a["id"] == aid), "Unknown"),
                "description": next((a["description"] for a in ACHIEVEMENT_DEFINITIONS if a["id"] == aid), ""),
                "icon": next((a["icon"] for a in ACHIEVEMENT_DEFINITIONS if a["id"] == aid), "🏆")
            }
            for aid in achievement_ids
        ]
        
        stats["achievements"] = achievements
        
        # Get recent activity
        cursor.execute('''
            SELECT 
                challenge, category, difficulty, completed, attempts, 
                UNIX_TIMESTAMP(timestamp) as timestamp_unix
            FROM user_attempts
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT 5
        ''', (username,))
        
        recent_activity = cursor.fetchall()
        
        # Convert MySQL objects to Python/JSON-serializable types
        formatted_activity = []
        for activity in recent_activity:
            formatted_activity.append({
                "challenge": activity['challenge'],
                "category": activity['category'],
                "difficulty": activity['difficulty'],
                "completed": bool(activity['completed']),
                "attempts": int(activity['attempts']),
                "timestamp": int(activity['timestamp_unix']) if activity['timestamp_unix'] else 0
            })
        
        stats["recent_activity"] = formatted_activity
        
        cursor.close()
        conn.close()
        
        print(f"✅ Successfully fetched stats for user: {username}")
        return jsonify(stats)
        
    except Exception as e:
        print(f"❌ Error getting user stats: {e}")
        traceback.print_exc()
        
        # Return empty stats instead of error
        empty_stats = {
            "challenges_attempted": 0,
            "challenges_completed": 0,
            "total_points": 0,
            "fastest_solve": None,
            "perfect_solves": 0,
            "category_count": {},
            "difficulty_count": {},
            "achievements": [],
            "recent_activity": []
        }
        return jsonify(empty_stats)

# Get leaderboard
@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    print("✅ Fetching leaderboard")
    
    try:
        conn = get_db_connection()
        if not conn:
            print("⚠️ Database connection failed in leaderboard route")
            return jsonify([])  # Return empty array instead of error
            
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT 
                user_id, username, total_points, challenges_completed
            FROM leaderboard
            ORDER BY total_points DESC, challenges_completed DESC
            LIMIT 10
        ''')
        
        leaderboard_data = cursor.fetchall()
        
        # Ensure we convert database types to JSON-serializable types
        formatted_data = []
        for i, entry in enumerate(leaderboard_data):
            formatted_data.append({
                "rank": i + 1,
                "user_id": entry['user_id'],
                "username": entry['username'],
                "points": int(entry['total_points']),
                "challenges_completed": int(entry['challenges_completed'])
            })
        
        cursor.close()
        conn.close()
        
        print(f"✅ Successfully fetched leaderboard with {len(formatted_data)} entries")
        return jsonify(formatted_data)
        
    except Exception as e:
        print(f"❌ Error getting leaderboard: {e}")
        traceback.print_exc()
        return jsonify([])  # Return empty array instead of error

@app.route('/generate_ctf', methods=['GET'])
def generate_ctf():
    difficulty = request.args.get('difficulty', '')
    category = request.args.get('category', '')
    
    if not difficulty or not category:
        return jsonify({'error': 'Both difficulty and category are required'})
    
    try:
        result = ctf_model.generate(difficulty, category)
        return jsonify(result)
    except Exception as e:
        print(f"❌ Error generating challenge: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate challenge: {str(e)}'})

@app.route('/get_hint', methods=['GET'])
def get_hint():
    try:
        result = ctf_model.get_hints()
        return jsonify(result)
    except Exception as e:
        print(f"❌ Error fetching hint: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Failed to fetch hint: {str(e)}'})

@app.route('/get_solution', methods=['GET'])
def get_solution():
    try:
        result = ctf_model.get_solution()
        return jsonify(result)
    except Exception as e:
        print(f"❌ Error fetching solution: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Failed to fetch solution: {str(e)}'})

@app.route('/check_flag', methods=['POST'])
def check_flag():
    data = request.json
    flag = data.get('flag')
    
    if not flag:
        return jsonify({'result': '⚠️ Please submit a valid flag'})
    
    try:
        # Use the CTF model to check the flag
        result = ctf_model.check_flag(flag)
        return jsonify(result)
    except Exception as e:
        print(f"❌ Error checking flag: {e}")
        traceback.print_exc()
        return jsonify({'result': f'⚠️ Error processing flag: {str(e)}'})

@app.route('/get_difficulty_levels', methods=['GET'])
def get_difficulty_levels():
    from ctf import DIFFICULTY_LEVELS
    return jsonify({'difficulty_levels': DIFFICULTY_LEVELS})

@app.route('/get_categories', methods=['GET'])
def get_categories():
    from ctf import CTF_CATEGORIES
    return jsonify({'categories': CTF_CATEGORIES})

@app.route('/', methods=['GET'])
def index():
    return jsonify({'status': 'CyberSensei CTF API is running'})

# Add at the end of the file
if __name__ == "__main__":
    # Make sure database is initialized
    init_db()
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True) 