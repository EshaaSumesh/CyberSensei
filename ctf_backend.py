from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import mysql.connector
import time
import traceback

# Import CTF challenge generator
try:
    from ctf import CTFChallengeModel, CTF_CATEGORIES, DIFFICULTY_LEVELS
except ImportError as e:
    print(f"Error importing CTF module: {e}")
    exit(1)

# Initialize Flask App
app = Flask(__name__)
CORS(app)

# Set API Key directly (avoid dependency on external config)
API_KEY = "AIzaSyDBUkjIXf1jhNdx2z6H2ZsJqDC1dpXPV68"
genai.configure(api_key=API_KEY)

# Points system configuration
POINTS_CONFIG = {
    "Beginner": {
        "base": 100,
        "time_bonus_threshold": 300,  # 5 minutes
        "time_bonus": 50,
        "attempts_penalty": 25
    },
    "Intermediate": {
        "base": 200,
        "time_bonus_threshold": 600,  # 10 minutes
        "time_bonus": 100,
        "attempts_penalty": 40
    },
    "Advanced": {
        "base": 300,
        "time_bonus_threshold": 900,  # 15 minutes
        "time_bonus": 150,
        "attempts_penalty": 60
    }
}

# Achievement configuration
ACHIEVEMENTS = {
    "first_blood": {"name": "First Blood", "description": "Solve your first challenge", "icon": "🩸", "points": 50},
    "beginner_master": {"name": "Beginner Master", "description": "Solve 5 beginner challenges", "icon": "🔰", "points": 100},
    "intermediate_master": {"name": "Intermediate Master", "description": "Solve 5 intermediate challenges", "icon": "🥈", "points": 200},
    "advanced_master": {"name": "Advanced Master", "description": "Solve 5 advanced challenges", "icon": "🥇", "points": 300},
    "speed_demon": {"name": "Speed Demon", "description": "Solve a challenge in under 2 minutes", "icon": "⚡", "points": 150},
    "no_hints": {"name": "No Help Needed", "description": "Solve a challenge without using hints", "icon": "🧠", "points": 100},
    "category_master": {"name": "Category Master", "description": "Solve at least one challenge in each category", "icon": "🏆", "points": 500},
    "perfect_score": {"name": "Perfect Score", "description": "Solve a challenge on first attempt", "icon": "💯", "points": 75}
}

try:
    # Initialize database
    db = Database(host="localhost", user="root", password="Chainsawman21", database="ctf_data")
    print("✅ Database connection successful")
except Exception as e:
    print(f"⚠️ Database connection error: {e}")
    print("Continuing without database...")
    db = None

# Initialize CTF model
ctf_model = CTFChallengeModel()
print("✅ CTF model initialized")

def init_db():
    """Initialize the MySQL database to store user attempts."""
    if db is None:
        print("⚠️ Skipping database initialization - no connection")
        return
        
    try:
        # User Attempts table
        db.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_attempts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255),
                category VARCHAR(255),
                challenge TEXT,
                correct_answer TEXT,
                user_answer TEXT,
                attempts INT,
                time_taken FLOAT,
                success BOOLEAN,
                points INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User Profile table
        db.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id VARCHAR(255) PRIMARY KEY,
                total_points INT DEFAULT 0,
                challenges_completed INT DEFAULT 0,
                beginner_completed INT DEFAULT 0,
                intermediate_completed INT DEFAULT 0,
                advanced_completed INT DEFAULT 0,
                fastest_time FLOAT DEFAULT NULL,
                consecutive_days INT DEFAULT 0,
                last_active DATE DEFAULT NULL
            )
        ''')
        
        # User Achievements table
        db.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255),
                achievement_id VARCHAR(255),
                achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, achievement_id)
            )
        ''')
        
        # Leaderboard table (for optimized leaderboard queries)
        db.cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaderboard (
                user_id VARCHAR(255) PRIMARY KEY,
                username VARCHAR(255),
                total_points INT DEFAULT 0,
                challenges_completed INT DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')
        
        db.connection.commit()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Error initializing database: {e}")
        traceback.print_exc()

def calculate_points(difficulty, time_taken, attempts):
    """Calculate points earned for solving a challenge."""
    config = POINTS_CONFIG.get(difficulty, POINTS_CONFIG["Beginner"])
    
    # Base points for difficulty
    points = config["base"]
    
    # Time bonus if completed quickly
    if time_taken < config["time_bonus_threshold"]:
        points += config["time_bonus"]
    
    # Penalty for multiple attempts
    if attempts > 1:
        points -= (attempts - 1) * config["attempts_penalty"]
    
    # Ensure minimum points
    return max(points, 50)

def check_achievements(user_id):
    """Check and award new achievements for a user."""
    if db is None:
        return []
    
    new_achievements = []
    
    try:
        # Get user's completed challenges
        db.cursor.execute('''
            SELECT difficulty, category, time_taken, attempts 
            FROM user_attempts 
            WHERE user_id = %s AND success = 1
        ''', (user_id,))
        challenges = db.cursor.fetchall()
        
        # Get user profile
        db.cursor.execute('SELECT * FROM user_profiles WHERE user_id = %s', (user_id,))
        profile = db.cursor.fetchone()
        
        if not profile:
            return []
        
        # Get already achieved achievements
        db.cursor.execute('SELECT achievement_id FROM user_achievements WHERE user_id = %s', (user_id,))
        existing_achievements = [row[0] for row in db.cursor.fetchall()]
        
        # Check for first_blood
        if len(challenges) > 0 and "first_blood" not in existing_achievements:
            award_achievement(user_id, "first_blood")
            new_achievements.append(ACHIEVEMENTS["first_blood"])
        
        # Check for beginner_master
        beginner_count = sum(1 for c in challenges if c[0] == "Beginner")
        if beginner_count >= 5 and "beginner_master" not in existing_achievements:
            award_achievement(user_id, "beginner_master")
            new_achievements.append(ACHIEVEMENTS["beginner_master"])
        
        # Check for intermediate_master
        intermediate_count = sum(1 for c in challenges if c[0] == "Intermediate")
        if intermediate_count >= 5 and "intermediate_master" not in existing_achievements:
            award_achievement(user_id, "intermediate_master")
            new_achievements.append(ACHIEVEMENTS["intermediate_master"])
        
        # Check for advanced_master
        advanced_count = sum(1 for c in challenges if c[0] == "Advanced")
        if advanced_count >= 5 and "advanced_master" not in existing_achievements:
            award_achievement(user_id, "advanced_master")
            new_achievements.append(ACHIEVEMENTS["advanced_master"])
        
        # Check for speed_demon
        if any(c[2] < 120 for c in challenges) and "speed_demon" not in existing_achievements:
            award_achievement(user_id, "speed_demon")
            new_achievements.append(ACHIEVEMENTS["speed_demon"])
        
        # Check for perfect_score
        if any(c[3] == 1 for c in challenges) and "perfect_score" not in existing_achievements:
            award_achievement(user_id, "perfect_score")
            new_achievements.append(ACHIEVEMENTS["perfect_score"])
        
        # Check for category_master
        completed_categories = {c[1] for c in challenges}
        if len(completed_categories) >= len(CTF_CATEGORIES) and "category_master" not in existing_achievements:
            award_achievement(user_id, "category_master")
            new_achievements.append(ACHIEVEMENTS["category_master"])
        
        return new_achievements
        
    except Exception as e:
        print(f"❌ Error checking achievements: {e}")
        return []

def award_achievement(user_id, achievement_id):
    """Award an achievement to a user and update their total points."""
    if db is None or achievement_id not in ACHIEVEMENTS:
        return False
    
    try:
        # Add achievement to user_achievements
        db.cursor.execute('''
            INSERT IGNORE INTO user_achievements (user_id, achievement_id)
            VALUES (%s, %s)
        ''', (user_id, achievement_id))
        
        # Update user's total points
        points = ACHIEVEMENTS[achievement_id]["points"]
        db.cursor.execute('''
            UPDATE user_profiles 
            SET total_points = total_points + %s 
            WHERE user_id = %s
        ''', (points, user_id))
        
        # Update leaderboard
        db.cursor.execute('''
            UPDATE leaderboard 
            SET total_points = total_points + %s 
            WHERE user_id = %s
        ''', (points, user_id))
        
        db.connection.commit()
        return True
    except Exception as e:
        print(f"❌ Error awarding achievement: {e}")
        return False

def update_user_profile(user_id, username, challenge_result):
    """Update user profile statistics after a challenge."""
    if db is None:
        return
    
    try:
        # Ensure user exists in user_profiles
        db.cursor.execute('''
            INSERT IGNORE INTO user_profiles (user_id, last_active) 
            VALUES (%s, CURDATE())
        ''', (user_id,))
        
        # Ensure user exists in leaderboard
        db.cursor.execute('''
            INSERT IGNORE INTO leaderboard (user_id, username) 
            VALUES (%s, %s)
        ''', (user_id, username))
        
        if challenge_result.get("success", 0) == 1:
            # Extract data
            points = challenge_result.get("points", 0)
            difficulty = challenge_result.get("difficulty", "Beginner")
            time_taken = challenge_result.get("time_taken", 0)
            
            # Update stats based on completed challenge
            db.cursor.execute('''
                UPDATE user_profiles SET 
                total_points = total_points + %s,
                challenges_completed = challenges_completed + 1,
                last_active = CURDATE(),
                fastest_time = CASE 
                    WHEN fastest_time IS NULL THEN %s 
                    WHEN %s < fastest_time THEN %s 
                    ELSE fastest_time 
                END
            ''', (points, time_taken, time_taken, time_taken))
            
            # Update difficulty-specific counters
            if difficulty == "Beginner":
                db.cursor.execute('''
                    UPDATE user_profiles SET beginner_completed = beginner_completed + 1
                    WHERE user_id = %s
                ''', (user_id,))
            elif difficulty == "Intermediate":
                db.cursor.execute('''
                    UPDATE user_profiles SET intermediate_completed = intermediate_completed + 1
                    WHERE user_id = %s
                ''', (user_id,))
            elif difficulty == "Advanced":
                db.cursor.execute('''
                    UPDATE user_profiles SET advanced_completed = advanced_completed + 1
                    WHERE user_id = %s
                ''', (user_id,))
            
            # Update leaderboard
            db.cursor.execute('''
                UPDATE leaderboard SET 
                total_points = total_points + %s,
                challenges_completed = challenges_completed + 1
                WHERE user_id = %s
            ''', (points, user_id))
        
        # Update consecutive days streak
        db.cursor.execute('''
            UPDATE user_profiles SET
            consecutive_days = CASE 
                WHEN DATEDIFF(CURDATE(), last_active) = 1 THEN consecutive_days + 1
                WHEN DATEDIFF(CURDATE(), last_active) = 0 THEN consecutive_days
                ELSE 1
            END,
            last_active = CURDATE()
            WHERE user_id = %s
        ''', (user_id,))
        
        db.connection.commit()
    except Exception as e:
        print(f"❌ Error updating user profile: {e}")
        traceback.print_exc()

@app.route("/get_categories", methods=["GET"])
def get_categories():
    """Return available CTF categories."""
    print("GET /get_categories - Returning categories")
    return jsonify({"categories": CTF_CATEGORIES})

@app.route("/get_difficulty_levels", methods=["GET"])
def get_difficulty_levels():
    """Return available difficulty levels."""
    print("GET /get_difficulty_levels - Returning difficulty levels")
    return jsonify({"difficulty_levels": DIFFICULTY_LEVELS})

@app.route("/generate_ctf", methods=["GET"])
def generate_ctf():
    print("GET /generate_ctf - Generating new challenge")
    difficulty = request.args.get("difficulty", "Beginner")
    category = request.args.get("category", "Cryptography")
    
    print(f"Generating challenge with difficulty: {difficulty}, category: {category}")
    
    try:
        challenge_data = ctf_model.generate(difficulty, category)
        print(f"Challenge generated successfully: {challenge_data.get('category')}")
        return jsonify(challenge_data)
    except Exception as e:
        error_msg = f"Error generating challenge: {str(e)}"
        traceback_str = traceback.format_exc()
        print(f"❌ {error_msg}")
        print(traceback_str)
        return jsonify({"error": error_msg}), 500

@app.route("/get_hint", methods=["GET"])
def get_hint():
    """Provide a hint for the current challenge."""
    print("GET /get_hint - Fetching hint")
    try:
        hint_data = ctf_model.get_hints()
        if "error" in hint_data:
            print(f"❌ Error fetching hint: {hint_data['error']}")
            return jsonify({"error": hint_data["error"]}), 400
        print("✅ Hint fetched successfully")
        return jsonify(hint_data)
    except Exception as e:
        error_msg = f"Error fetching hint: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.route("/get_solution", methods=["GET"])
def get_solution():
    """Return the solution for the current challenge."""
    print("GET /get_solution - Fetching solution")
    try:
        solution_data = ctf_model.get_solution()
        if "error" in solution_data:
            print(f"❌ Error fetching solution: {solution_data['error']}")
            return jsonify({"error": solution_data["error"]}), 400
        print("✅ Solution fetched successfully")
        return jsonify(solution_data)
    except Exception as e:
        error_msg = f"Error fetching solution: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.route("/check_flag", methods=["POST"])
def check_flag():
    """Check if the provided flag is correct."""
    print("POST /check_flag - Checking flag")
    try:
        data = request.json
        user_flag = data.get("flag", "")
        print(f"Checking flag: {user_flag[:10]}...")
        
        result = ctf_model.check_flag(user_flag)
        print(f"Flag check result: {result['result']}")
        return jsonify(result)
    except Exception as e:
        error_msg = f"Error checking flag: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.route("/submit_answer", methods=["POST"])
def submit_answer():
    """Evaluate the user's answer, track attempts, and provide feedback."""
    print("POST /submit_answer - Recording user attempt")
    
    try:
        data = request.json
        user_id = data.get("user_id")
        username = data.get("username", user_id)
        category = data.get("category")
        difficulty = data.get("difficulty")
        challenge = data.get("challenge")
        user_answer = data.get("user_answer")
        attempts = data.get("attempts", 0)
        start_time = float(data.get("start_time"))
        time_taken = time.time() - start_time
        
        # Check if the answer is correct using the ctf_model
        check_result = ctf_model.check_flag(user_answer)
        success = 1 if "✅ Correct" in check_result.get("result", "") else 0
        
        # Calculate points
        points = 0
        if success:
            points = calculate_points(difficulty, time_taken, attempts)
        
        result = {
            "success": success, 
            "feedback": check_result.get("result", "Invalid response"),
            "attempts": attempts, 
            "time_taken": time_taken,
            "points": points,
            "difficulty": difficulty
        }
        
        if db is not None:
            try:
                # Store attempt in the database
                db.cursor.execute('''
                    INSERT INTO user_attempts (
                        user_id, category, challenge, correct_answer, user_answer, 
                        attempts, time_taken, success, points
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
                    (user_id, category, challenge, "", user_answer, attempts, time_taken, success, points)
                )
                
                # Update user profile and leaderboard
                if success:
                    update_user_profile(user_id, username, result)
                    
                    # Check for new achievements
                    new_achievements = check_achievements(user_id)
                    if new_achievements:
                        result["achievements"] = new_achievements
                
                db.connection.commit()
                print(f"✅ User attempt recorded: user={user_id}, success={success}, points={points}")
            except Exception as e:
                print(f"❌ Error recording attempt in database: {e}")
                traceback.print_exc()
        else:
            print("⚠️ No database connection, attempt not recorded")
        
        return jsonify(result)
    except Exception as e:
        error_msg = f"Error submitting answer: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return jsonify({"error": error_msg}), 500

@app.route("/get_leaderboard", methods=["GET"])
def get_leaderboard():
    """Get the global leaderboard."""
    print("GET /get_leaderboard - Fetching leaderboard")
    
    if db is None:
        return jsonify({"error": "Database connection not available"}), 500
    
    try:
        limit = int(request.args.get("limit", 10))
        
        db.cursor.execute('''
            SELECT user_id, username, total_points, challenges_completed
            FROM leaderboard
            ORDER BY total_points DESC, challenges_completed DESC
            LIMIT %s
        ''', (limit,))
        
        results = db.cursor.fetchall()
        
        leaderboard = [{
            "user_id": row[0],
            "username": row[1],
            "total_points": row[2],
            "challenges_completed": row[3],
            "rank": idx + 1
        } for idx, row in enumerate(results)]
        
        return jsonify({"leaderboard": leaderboard})
    except Exception as e:
        error_msg = f"Error fetching leaderboard: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.route("/get_user_stats", methods=["GET"])
def get_user_stats():
    """Get detailed statistics for a specific user."""
    print("GET /get_user_stats - Fetching user stats")
    
    if db is None:
        return jsonify({"error": "Database connection not available"}), 500
    
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        # Get user profile
        db.cursor.execute('''
            SELECT 
                total_points, challenges_completed, beginner_completed, 
                intermediate_completed, advanced_completed, fastest_time, 
                consecutive_days
            FROM user_profiles 
            WHERE user_id = %s
        ''', (user_id,))
        
        profile = db.cursor.fetchone()
        if not profile:
            return jsonify({"error": "User not found"}), 404
        
        # Get user's rank
        db.cursor.execute('''
            SELECT COUNT(*) + 1 
            FROM leaderboard 
            WHERE total_points > (SELECT total_points FROM leaderboard WHERE user_id = %s)
        ''', (user_id,))
        
        rank = db.cursor.fetchone()[0]
        
        # Get user achievements
        db.cursor.execute('''
            SELECT achievement_id 
            FROM user_achievements 
            WHERE user_id = %s
        ''', (user_id,))
        
        achievement_ids = [row[0] for row in db.cursor.fetchall()]
        achievements = [
            {**ACHIEVEMENTS[aid], "id": aid} 
            for aid in achievement_ids
            if aid in ACHIEVEMENTS
        ]
        
        # Get category completion stats
        db.cursor.execute('''
            SELECT category, COUNT(*) as completed
            FROM user_attempts
            WHERE user_id = %s AND success = 1
            GROUP BY category
        ''', (user_id,))
        
        category_stats = {row[0]: row[1] for row in db.cursor.fetchall()}
        
        # Calculate completion percentage for each category
        categories_completion = {}
        for cat in CTF_CATEGORIES:
            completed = category_stats.get(cat, 0)
            categories_completion[cat] = {
                "completed": completed,
                "percentage": min(100, int(completed / 5 * 100))  # Assuming 5 challenges per category is "complete"
            }
        
        # Get recent activity
        db.cursor.execute('''
            SELECT 
                category, difficulty, success, time_taken, points, created_at
            FROM user_attempts
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 10
        ''', (user_id,))
        
        recent_activity = [{
            "category": row[0],
            "difficulty": row[1],
            "success": bool(row[2]),
            "time_taken": row[3],
            "points": row[4],
            "date": row[5].isoformat() if row[5] else None
        } for row in db.cursor.fetchall()]
        
        return jsonify({
            "user_id": user_id,
            "rank": rank,
            "profile": {
                "total_points": profile[0],
                "challenges_completed": profile[1],
                "beginner_completed": profile[2],
                "intermediate_completed": profile[3],
                "advanced_completed": profile[4],
                "fastest_time": profile[5],
                "consecutive_days": profile[6]
            },
            "achievements": achievements,
            "categories_completion": categories_completion,
            "recent_activity": recent_activity
        })
    except Exception as e:
        error_msg = f"Error fetching user stats: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return jsonify({"error": error_msg}), 500

@app.route("/get_achievements", methods=["GET"])
def get_achievements():
    """Get all available achievements."""
    print("GET /get_achievements - Fetching achievement list")
    
    try:
        achievements_list = []
        for aid, achievement in ACHIEVEMENTS.items():
            achievements_list.append({
                "id": aid,
                **achievement
            })
        
        return jsonify({"achievements": achievements_list})
    except Exception as e:
        error_msg = f"Error fetching achievements: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.route("/debug/routes", methods=["GET"])
def debug_routes():
    """Returns all registered routes for debugging."""
    routes = {rule.rule: list(rule.methods) for rule in app.url_map.iter_rules()}
    return jsonify(routes)

@app.route("/", methods=["GET"])
def home():
    """Basic health check endpoint."""
    return jsonify({
        "status": "online",
        "message": "CTF backend server is running",
        "api_endpoints": {
            "get_categories": "/get_categories",
            "get_difficulty_levels": "/get_difficulty_levels",
            "generate_ctf": "/generate_ctf?difficulty=Beginner&category=Cryptography",
            "check_flag": "/check_flag (POST)",
            "get_hint": "/get_hint",
            "get_solution": "/get_solution"
        }
    })

if __name__ == "__main__":
    # Handle database error gracefully
    try:
        from db import Database
        print("✅ Database module imported successfully")
        init_db()
    except ImportError:
        print("⚠️ Database module not found, continuing without database functionality")
        db = None
    except Exception as e:
        print(f"⚠️ Error with database: {e}")
        db = None
    
    # Run the app
    print("🚀 Starting CTF backend server...")
    app.run(debug=True, port=5000)
