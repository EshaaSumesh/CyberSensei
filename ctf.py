import google.generativeai as genai
import random
import sys
import time

# ✅ Fix UnicodeEncodeError for Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    # For Python versions that don't support reconfigure
    pass

# ✅ Set API Key Correctly
API_KEY = "AIzaSyDBUkjIXf1jhNdx2z6H2ZsJqDC1dpXPV68"  # Replace with your actual API key
genai.configure(api_key=API_KEY)

# ✅ Define CTF Challenge Categories
CTF_CATEGORIES = [
    "Cryptography", "Forensics", "Web Exploitation", "Reverse Engineering",
    "Binary Exploitation", "Steganography", "OSINT", "Networking", "Miscellaneous"
]

# ✅ Define Difficulty Levels
DIFFICULTY_LEVELS = ["Beginner", "Intermediate", "Advanced"]

class CTFChallengeModel:
    def __init__(self):
        self.current_challenge = None  # Stores current challenge details
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def generate(self, difficulty, category):
        """Generate a CTF challenge based on difficulty and category."""
        if difficulty not in DIFFICULTY_LEVELS:
            return {"error": "Invalid difficulty level. Choose from Beginner, Intermediate, Advanced."}
        if category not in CTF_CATEGORIES:
            return {"error": f"Invalid category. Choose from: {', '.join(CTF_CATEGORIES)}"}

        try:
            prompt = (
                f"Generate a {difficulty}-level {category} CTF challenge. "
                f"Provide only the problem statement and expected flag format (without revealing the flag)."
            )
            response = self.model.generate_content(prompt)

            challenge_text = response.text if response and response.text else "⚠️ No challenge generated."

            # Store challenge state
            self.current_challenge = {
                "difficulty": difficulty,
                "category": category,
                "challenge": challenge_text,
                "hints": [],
                "solution": None
            }

            return {"category": category, "difficulty": difficulty, "challenge": challenge_text}

        except Exception as e:
            return {"error": f"❌ Error in challenge generation: {e}"}

    def get_hints(self):
        """Fetch hints for the current challenge."""
        if not self.current_challenge:
            return {"error": "No challenge generated. Please generate a challenge first."}

        if not self.current_challenge["hints"]:
            try:
                prompt = f"Provide helpful hints (without the solution) for the following challenge:\n\n{self.current_challenge['challenge']}"
                response = self.model.generate_content(prompt)

                hints = response.text.split("\n") if response and response.text else ["⚠️ No hints available."]
                self.current_challenge["hints"] = hints
            except Exception as e:
                return {"error": f"❌ Error in fetching hints: {e}"}

        return {"hints": self.current_challenge["hints"]}

    def get_solution(self):
        """Fetch the solution for the challenge."""
        if not self.current_challenge:
            return {"error": "No challenge generated. Please generate a challenge first."}

        if not self.current_challenge["solution"]:
            try:
                prompt = f"Provide ONLY the solution for the following challenge:\n\n{self.current_challenge['challenge']}"
                response = self.model.generate_content(prompt)

                solution = response.text if response and response.text else "⚠️ No solution available."
                self.current_challenge["solution"] = solution
            except Exception as e:
                return {"error": f"❌ Error in fetching solution: {e}"}

        return {"solution": self.current_challenge["solution"]}

    def check_flag(self, user_flag):
        """Validate the user-entered flag using AI."""
        if not self.current_challenge:
            return {"error": "No challenge generated. Please generate a challenge first."}

        try:
            # Ask AI to evaluate if the answer is correct for this specific challenge
            prompt = f"""
            For the following CTF challenge:
            
            {self.current_challenge['challenge']}
            
            Evaluate if this submitted answer is correct: "{user_flag}"
            Respond with only "CORRECT" or "INCORRECT" and a brief explanation.
            """
            
            response = self.model.generate_content(prompt)
            
            result_text = response.text if response and response.text else "Unable to validate answer."
            
            if result_text.upper().strip().startswith("CORRECT"):
                stored_challenge = self.current_challenge
                self.current_challenge = None  # Reset after success
                return {"result": f"✅ Correct! You solved the challenge.\n\nAI analysis: {result_text}"}
            else:
                return {"result": f"❌ Incorrect flag. Try again or request hints.\n\nAI analysis: {result_text}"}
                
        except Exception as e:
            return {"error": f"❌ Error in flag validation: {e}"}

    def generate_personalized_challenge(self, user_data):
        """Generate a challenge personalized to user's strengths/weaknesses."""
        try:
            # Extract info about the user
            strong_categories = user_data.get("strong_categories", [])
            weak_categories = user_data.get("weak_categories", [])
            completed_challenges = user_data.get("completed_challenges", [])
            user_level = user_data.get("skill_level", "Beginner")
            
            prompt = f"""
            Create a CTF challenge for a user with the following profile:
            - Strong in: {', '.join(strong_categories) if strong_categories else 'Not enough data'}
            - Needs improvement in: {', '.join(weak_categories) if weak_categories else 'Not enough data'}
            - Has completed {len(completed_challenges)} challenges
            - Overall skill level: {user_level}
            
            Create a challenge that:
            1. Builds on their strengths but pushes them slightly
            2. Incorporates an aspect of an area they need to improve
            3. Is different from challenges they've already seen
            4. Is appropriate for their overall skill level
            
            Provide only the problem statement and expected flag format (without revealing the flag).
            """
            
            response = self.model.generate_content(prompt)
            
            challenge_text = response.text if response and response.text else "⚠️ No challenge generated."
            
            # Determine most appropriate category and difficulty
            category_prompt = f"""
            Based on this challenge:
            
            {challenge_text}
            
            Which single category best describes it from this list: {', '.join(CTF_CATEGORIES)}?
            And which difficulty level best describes it from this list: {', '.join(DIFFICULTY_LEVELS)}?
            
            Format response as:
            CATEGORY: [category]
            DIFFICULTY: [difficulty]
            """
            
            cat_response = self.model.generate_content(category_prompt)
            
            category = None
            difficulty = None
            
            for line in cat_response.text.split('\n'):
                if line.startswith('CATEGORY:'):
                    category = line.replace('CATEGORY:', '').strip()
                elif line.startswith('DIFFICULTY:'):
                    difficulty = line.replace('DIFFICULTY:', '').strip()
            
            # Default values if AI doesn't return valid options
            if category not in CTF_CATEGORIES:
                category = random.choice(weak_categories) if weak_categories else random.choice(CTF_CATEGORIES)
                
            if difficulty not in DIFFICULTY_LEVELS:
                difficulty = user_level if user_level in DIFFICULTY_LEVELS else "Beginner"
            
            # Store challenge state
            self.current_challenge = {
                "difficulty": difficulty,
                "category": category,
                "challenge": challenge_text,
                "hints": [],
                "solution": None,
                "personalized": True
            }
            
            return {
                "category": category, 
                "difficulty": difficulty, 
                "challenge": challenge_text,
                "personalized": True
            }
            
        except Exception as e:
            return {"error": f"❌ Error in personalized challenge generation: {e}"}

    def assess_user_skills(self, user_history):
        """Generate an AI assessment of user skills based on their history."""
        try:
            if not user_history:
                return {"error": "Insufficient data for skill assessment"}
                
            # Format history for the AI
            history_text = "\n".join([
                f"Challenge: {h['category']} ({h['difficulty']}), Success: {'Yes' if h['success'] else 'No'}, " 
                f"Attempts: {h['attempts']}, Time: {h['time_taken']}s"
                for h in user_history
            ])
            
            prompt = f"""
            Analyze this CTF challenge history to assess the user's cybersecurity skills:
            
            {history_text}
            
            For your analysis, provide:
            1. Overall skill assessment (Beginner/Intermediate/Advanced)
            2. Strongest category with explanation
            3. Category needing most improvement with explanation
            4. Three specific skills they demonstrate proficiency in
            5. Three specific recommendations for improvement
            6. A learning path suggestion
            """
            
            response = self.model.generate_content(prompt)
            
            return {"assessment": response.text}
            
        except Exception as e:
            return {"error": f"❌ Error in skill assessment: {e}"}

    def get_learning_resources(self, topic, concept):
        """Provide AI-generated learning resources for specific security concepts."""
        try:
            prompt = f"""
            Generate a concise learning guide about {concept} in {topic} for CTF challenges.
            Include:
            1. Brief explanation of the concept
            2. Common techniques used in CTF challenges
            3. One simple example with explanation
            4. Recommended tools or resources
            """
            
            response = self.model.generate_content(prompt)
            
            return {"learning_guide": response.text}
            
        except Exception as e:
            return {"error": f"❌ Error generating learning resources: {e}"}

    def analyze_code_sample(self, code, language, question=None):
        """Provide AI analysis of code samples for learning purposes."""
        try:
            prompt = f"""
            Analyze this {language} code for security vulnerabilities or CTF-relevant insights:
            
            ```{language}
            {code}
            ```
            """
            
            if question:
                prompt += f"\n\nSpecifically address this question: {question}"
            else:
                prompt += """
                Provide:
                1. A security analysis identifying potential vulnerabilities
                2. Explanation of what the code does
                3. Potential CTF challenge approaches related to this code
                4. Tips for solving similar challenges
                """
            
            response = self.model.generate_content(prompt)
            
            return {"analysis": response.text}
            
        except Exception as e:
            return {"error": f"❌ Error in code analysis: {e}"}

    def get_challenge_coaching(self, user_attempt, hint_level=0):
        """Provide AI coaching based on user's incorrect attempt."""
        if not self.current_challenge:
            return {"error": "No challenge is currently active"}
            
        try:
            hint_types = [
                "gentle nudge in right direction without revealing much",
                "more specific guidance addressing likely misconception",
                "substantial hint that points directly toward solution approach"
            ]
            
            hint_type = hint_types[min(hint_level, len(hint_types)-1)]
            
            prompt = f"""
            For this CTF challenge:
            
            {self.current_challenge['challenge']}
            
            The user submitted this incorrect answer:
            "{user_attempt}"
            
            Provide a {hint_type}.
            Focus on helping them understand their mistake or misconception without giving away the solution.
            """
            
            response = self.model.generate_content(prompt)
            
            return {"coaching": response.text}
            
        except Exception as e:
            return {"error": f"❌ Error providing coaching: {e}"}

    def recommend_next_challenge(self, user_history):
        """Use AI to recommend the next best challenge based on user history."""
        try:
            # Format the user's previous attempts and successes
            history_text = "\n".join([
                f"Challenge: {h['category']} ({h['difficulty']}), Success: {'Yes' if h['success'] else 'No'}, " 
                f"Attempts: {h['attempts']}, Time: {h['time_taken']}s"
                for h in user_history
            ])
            
            prompt = f"""
            Based on this user's CTF challenge history:
            
            {history_text}
            
            Recommend the next challenge category and difficulty that would be 
            most beneficial for their learning. Consider their strengths, weaknesses, 
            and potential areas for growth.
            
            Format your response as:
            CATEGORY: [category name]
            DIFFICULTY: [difficulty level]
            REASONING: [brief explanation]
            """
            
            response = self.model.generate_content(prompt)
            
            # Parse the response
            category = None
            difficulty = None
            reasoning = None
            
            for line in response.text.split('\n'):
                if line.startswith('CATEGORY:'):
                    category = line.replace('CATEGORY:', '').strip()
                elif line.startswith('DIFFICULTY:'):
                    difficulty = line.replace('DIFFICULTY:', '').strip()
                elif line.startswith('REASONING:'):
                    reasoning = line.replace('REASONING:', '').strip()
            
            return {
                "category": category,
                "difficulty": difficulty,
                "reasoning": reasoning
            }
            
        except Exception as e:
            return {"error": f"❌ Error in challenge recommendation: {e}"}

    def explain_challenge(self):
        """Generate an educational explanation after challenge completion."""
        if not self.current_challenge or not self.current_challenge.get("solution"):
            try:
                # If we don't have a solution yet, get one first
                self.get_solution()
            except:
                return {"error": "No completed challenge to explain"}
            
        try:
            prompt = f"""
            For this CTF challenge:
            
            {self.current_challenge['challenge']}
            
            With solution:
            {self.current_challenge['solution']}
            
            Provide an educational explanation including:
            1. Core concepts this challenge teaches
            2. Step-by-step approach to solve it correctly
            3. Common techniques or tools relevant to this challenge
            4. How this relates to real-world cybersecurity
            5. Recommended resources to learn more about these concepts
            """
            
            response = self.model.generate_content(prompt)
            
            return {"explanation": response.text}
            
        except Exception as e:
            return {"error": f"❌ Error generating explanation: {e}"}

    def generate_performance_insights(self, user_data):
        """Generate AI-powered insights about user performance."""
        try:
            # Format user data for the AI
            user_summary = (
                f"Total challenges attempted: {user_data['total_attempted']}\n"
                f"Successful completions: {user_data['total_successful']}\n"
                f"Average attempts per challenge: {user_data['avg_attempts']:.1f}\n"
                f"Average completion time: {user_data['avg_time']:.1f}s\n"
                f"Categories attempted: {', '.join(user_data['categories_attempted'])}\n"
                f"Success by category: {user_data['category_success_rates']}\n"
            )
            
            prompt = f"""
            Based on this CTF user performance data:
            
            {user_summary}
            
            Generate insightful performance analytics including:
            1. Three key performance strengths
            2. Three specific areas for improvement
            3. Personalized learning strategy
            4. Two visualizations that would be most helpful (describe them)
            5. AI prediction of which categories they'll excel in next
            
            Keep insights specific, actionable, and data-driven.
            """
            
            response = self.model.generate_content(prompt)
            
            return {"insights": response.text}
            
        except Exception as e:
            return {"error": f"❌ Error generating performance insights: {e}"}


def interactive_ctf():
    """Interactive CTF challenge interface"""
    ctf_model = CTFChallengeModel()

    # Step 1: Ask for difficulty level
    print("\n🎮 Welcome to CyberSensei CTF Challenge Generator! 🎮\n")
    print("Select difficulty level:")
    for i, level in enumerate(DIFFICULTY_LEVELS, 1):
        print(f"{i}. {level}")
    
    while True:
        try:
            difficulty_choice = int(input("\nEnter the number for difficulty (1-3): "))
            if 1 <= difficulty_choice <= 3:
                difficulty = DIFFICULTY_LEVELS[difficulty_choice-1]
                break
            else:
                print("Please enter a number between 1 and 3.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Step 2: Ask for category
    print("\nSelect challenge category:")
    for i, category in enumerate(CTF_CATEGORIES, 1):
        print(f"{i}. {category}")
    
    while True:
        try:
            category_choice = int(input(f"\nEnter the number for category (1-{len(CTF_CATEGORIES)}): "))
            if 1 <= category_choice <= len(CTF_CATEGORIES):
                category = CTF_CATEGORIES[category_choice-1]
                break
            else:
                print(f"Please enter a number between 1 and {len(CTF_CATEGORIES)}.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Step 3: Generate challenge
    print(f"\n⏳ Generating {difficulty} level {category} challenge...\n")
    challenge_result = ctf_model.generate(difficulty, category)
    
    if "error" in challenge_result:
        print(f"Error: {challenge_result['error']}")
        return
    
    print("\n🚩 CHALLENGE 🚩")
    print("-" * 40)
    print(challenge_result["challenge"])
    print("-" * 40)
    
    # Step 4: Process user solutions and provide hints if needed
    hint_count = 0
    max_attempts = 3
    attempts = 0
    start_time = time.time()
    
    while attempts < max_attempts:
        user_flag = input("\nEnter your flag: ")
        check_result = ctf_model.check_flag(user_flag)
        
        if "error" in check_result:
            print(f"Error: {check_result['error']}")
            return
        
        print(check_result["result"])
        
        if "✅ Correct" in check_result["result"]:
            print("\n🎉 Congratulations! You've solved the challenge! 🎉")
            time_taken = time.time() - start_time
            print(f"Time taken: {time_taken:.1f} seconds")
            
            # Get educational explanation
            print("\n📚 LEARNING INSIGHTS:")
            print("-" * 40)
            explanation = ctf_model.explain_challenge()
            if "explanation" in explanation:
                print(explanation["explanation"])
            
            return
        
        attempts += 1
        if attempts < max_attempts:
            print(f"Attempts remaining: {max_attempts - attempts}")
            
            # Offer coaching based on last attempt
            coaching_choice = input("\nWould you like personalized coaching on your attempt? (y/n): ").lower()
            if coaching_choice.startswith('y'):
                coaching = ctf_model.get_challenge_coaching(user_flag, attempts-1)
                if "coaching" in coaching:
                    print(f"\n🧠 AI COACHING:")
                    print("-" * 40)
                    print(coaching["coaching"])
                    print("-" * 40)
            
            hint_choice = input("\nWould you like a hint? (y/n): ").lower()
            if hint_choice.startswith('y'):
                hints = ctf_model.get_hints()
                if "error" in hints:
                    print(f"Error: {hints['error']}")
                else:
                    if hint_count < len(hints["hints"]):
                        print(f"\n💡 HINT: {hints['hints'][hint_count]}")
                        hint_count += 1
                    else:
                        print("\n⚠️ No more hints available.")
    
    print("\n⏱️ Max attempts reached. Would you like to see the solution?")
    solution_choice = input("Show solution? (y/n): ").lower()
    if solution_choice.startswith('y'):
        solution = ctf_model.get_solution()
        if "error" in solution:
            print(f"Error: {solution['error']}")
        else:
            print("\n🔍 SOLUTION:")
            print("-" * 40)
            print(solution["solution"])
            print("-" * 40)
            
            # Offer learning resources
            learning_choice = input("\nWould you like learning resources to understand this better? (y/n): ").lower()
            if learning_choice.startswith('y'):
                learning = ctf_model.get_learning_resources(category, f"{category} CTF challenge")
                if "learning_guide" in learning:
                    print("\n📚 LEARNING RESOURCES:")
                    print("-" * 40)
                    print(learning["learning_guide"])
                    print("-" * 40)


# Run the interactive CTF when script is executed
if __name__ == "__main__":
    try:
        interactive_ctf()
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        print("Please check your internet connection and API key.")
