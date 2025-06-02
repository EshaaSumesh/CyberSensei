import React, { useState, useEffect } from "react";
import axios from "axios";
import UserStats from "./UserStats";

const ChatInterface = () => {
  // Challenge state
  const [challenge, setChallenge] = useState(null);
  const [userAnswer, setUserAnswer] = useState("");
  const [result, setResult] = useState("");
  const [attempts, setAttempts] = useState(0);
  const [startTime, setStartTime] = useState(null);
  const [username, setUsername] = useState("");
  
  // UI flow state
  const [step, setStep] = useState("difficulty"); // difficulty, category, challenge, result
  const [difficultyLevels, setDifficultyLevels] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedDifficulty, setSelectedDifficulty] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  
  // Hints and solution
  const [hints, setHints] = useState([]);
  const [showingHints, setShowingHints] = useState(false);
  const [currentHintIndex, setCurrentHintIndex] = useState(0);
  const [solution, setSolution] = useState("");
  const [showingSolution, setShowingSolution] = useState(false);
  
  // Loading and error states
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  
  // Points and achievements
  const [pointsEarned, setPointsEarned] = useState(0);
  const [totalPoints, setTotalPoints] = useState(0);
  const [newAchievements, setNewAchievements] = useState([]);
  const [showAchievementPopup, setShowAchievementPopup] = useState(false);
  
  // Navigation
  const [activeTab, setActiveTab] = useState("challenge"); // challenge or stats
  
  const MAX_ATTEMPTS = 3;
  const API_BASE_URL = "http://localhost:5000";

  useEffect(() => {
    // Fetch available difficulty levels and categories
    fetchDifficultyLevels();
    fetchCategories();
    // Check if backend is running
    checkBackendStatus();
  }, []);

  const checkBackendStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/`);
      console.log("Backend status:", response.data.status);
    } catch (error) {
      console.error("Backend connection error:", error);
      setErrorMessage("Cannot connect to the CTF backend. Please make sure the server is running.");
    }
  };

  const fetchDifficultyLevels = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API_BASE_URL}/get_difficulty_levels`);
      setDifficultyLevels(response.data.difficulty_levels);
      setErrorMessage("");
    } catch (error) {
      console.error("Error fetching difficulty levels", error);
      setErrorMessage("Failed to load difficulty levels. Please refresh the page or check the backend server.");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API_BASE_URL}/get_categories`);
      setCategories(response.data.categories);
      setErrorMessage("");
    } catch (error) {
      console.error("Error fetching categories", error);
      setErrorMessage("Failed to load categories. Please refresh the page or check the backend server.");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchChallenge = async () => {
    try {
      setIsLoading(true);
      setErrorMessage("");
      
      console.log(`Fetching challenge: difficulty=${selectedDifficulty}, category=${selectedCategory}`);
      const response = await axios.get(
        `${API_BASE_URL}/generate_ctf?difficulty=${encodeURIComponent(selectedDifficulty)}&category=${encodeURIComponent(selectedCategory)}`
      );
      
      console.log("Challenge response:", response.data);
      
      if (response.data.error) {
        setErrorMessage(`Error from server: ${response.data.error}`);
        return;
      }
      
      // Ensure challenge is stored correctly
      setChallenge({
        category: response.data.category, 
        difficulty: response.data.difficulty,
        question: response.data.challenge // Adjusted to match API response
      });

      setUserAnswer("");
      setResult("");
      setAttempts(0);
      setStartTime(Date.now() / 1000); // Capture start time
      setStep("challenge");
      setHints([]);
      setSolution("");
      setShowingHints(false);
      setCurrentHintIndex(0);
      setShowingSolution(false);
    } catch (error) {
      console.error("Error fetching challenge", error);
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        setErrorMessage(`Server error: ${error.response.data.error || error.response.status}`);
      } else if (error.request) {
        // The request was made but no response was received
        setErrorMessage("No response from server. Please check if the backend is running.");
      } else {
        // Something happened in setting up the request that triggered an Error
        setErrorMessage(`Error: ${error.message}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const fetchHint = async () => {
    try {
      const response = await axios.get("http://localhost:5000/get_hint");
      if (response.data.hints) {
        setHints(response.data.hints);
        setShowingHints(true);
      }
    } catch (error) {
      console.error("Error fetching hint", error);
    }
  };

  const fetchSolution = async () => {
    try {
      const response = await axios.get("http://localhost:5000/get_solution");
      if (response.data.solution) {
        setSolution(response.data.solution);
        setShowingSolution(true);
      }
    } catch (error) {
      console.error("Error fetching solution", error);
    }
  };

  const checkFlag = async () => {
    if (!username) {
      setResult("Please enter a username first.");
      return;
    }

    try {
      const response = await axios.post("http://localhost:5000/check_flag", {
        flag: userAnswer
      });

      setResult(response.data.result);
      
      if (response.data.result.includes("✅ Correct")) {
        // Submit to track progress
        const submitResponse = await axios.post("http://localhost:5000/submit_answer", {
          user_id: username, 
          username: username,
          category: challenge.category,
          challenge: challenge.question,
          difficulty: challenge.difficulty,
          user_answer: userAnswer,
          attempts: attempts + 1,
          start_time: startTime,
          result: response.data.result // Pass the result from check_flag
        });
        
        console.log("Submit response:", submitResponse.data);
        
        // Handle points and achievements
        if (submitResponse.data.points) {
          setPointsEarned(submitResponse.data.points);
          setTotalPoints(prev => prev + submitResponse.data.points);
        }
        
        if (submitResponse.data.achievements && submitResponse.data.achievements.length > 0) {
          setNewAchievements(submitResponse.data.achievements);
          setShowAchievementPopup(true);
          
          // Auto-hide achievement popup after 5 seconds
          setTimeout(() => {
            setShowAchievementPopup(false);
          }, 5000);
        }
        
        setStep("result");
      } else {
        const newAttempts = attempts + 1;
        setAttempts(newAttempts);
        
        // Submit to track progress even for failed attempts
        const submitResponse = await axios.post("http://localhost:5000/submit_answer", {
          user_id: username,
          username: username,
          category: challenge.category,
          challenge: challenge.question,
          difficulty: challenge.difficulty,
          user_answer: userAnswer,
          attempts: newAttempts,
          start_time: startTime,
          result: response.data.result // Pass the result from check_flag
        });
        
        console.log("Submit failed attempt response:", submitResponse.data);
        
        if (newAttempts >= MAX_ATTEMPTS) {
          setStep("result");
        }
      }
    } catch (error) {
      console.error("Error checking flag", error);
      setResult("Error checking flag: " + (error.response?.data?.error || error.message));
    }
  };

  const handleNextHint = () => {
    if (currentHintIndex < hints.length - 1) {
      setCurrentHintIndex(currentHintIndex + 1);
    }
  };

  const resetAndStartNew = () => {
    setStep("difficulty");
    setSelectedDifficulty("");
    setSelectedCategory("");
    setChallenge(null);
    setUserAnswer("");
    setResult("");
    setAttempts(0);
    setHints([]);
    setSolution("");
    setShowingHints(false);
    setCurrentHintIndex(0);
    setShowingSolution(false);
  };

  const renderDifficultySelection = () => {
    return (
      <div className="fade-in">
        <h2 className="cyber-section-header">Step 1: Select Difficulty Level</h2>
        {errorMessage && <div className="cyber-alert error">{errorMessage}</div>}
        
        {isLoading ? (
          <div className="cyber-spinner"></div>
        ) : (
          <div>
            {difficultyLevels.map((level) => (
              <button
                key={level}
                className={`cyber-button ${selectedDifficulty === level ? 'active' : ''}`}
                onClick={() => {
                  setSelectedDifficulty(level);
                  setStep("category");
                }}
              >
                {level}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderCategorySelection = () => {
    return (
      <div className="fade-in">
        <h2 className="cyber-section-header">Step 2: Select Challenge Category</h2>
        {errorMessage && <div className="cyber-alert error">{errorMessage}</div>}
        
        <div className="cyber-grid">
          {categories.map((category) => (
            <div 
              key={category}
              className={`cyber-card cyber-scanner ${selectedCategory === category ? 'active' : ''}`}
              onClick={() => {
                setSelectedCategory(category);
                fetchChallenge();
              }}
            >
              <div className="cyber-card-header neon-text">{category}</div>
              <div className="category-description">
                Master the art of {category.toLowerCase()} challenges
              </div>
            </div>
          ))}
        </div>
        
        <button
          className="cyber-button"
          onClick={() => setStep("difficulty")}
        >
          Back to Difficulty Selection
        </button>
      </div>
    );
  };

  const renderChallenge = () => {
    if (!challenge) return null;

    return (
      <div className="challenge-container fade-in">
        <div className="hud-element">
          Category: <span className="neon-text">{challenge.category}</span> | 
          Difficulty: <span className="neon-text">{challenge.difficulty}</span> |
          Attempts: <span className="neon-text">{attempts}/{MAX_ATTEMPTS}</span>
        </div>
        
        <div className="terminal-text">
          {challenge.question}
        </div>
        
        <div className="cyber-card">
          <div className="user-input-section">
            <label htmlFor="usernameInput" className="visually-hidden">Enter Username</label>
            <input
              id="usernameInput"
              type="text"
              className="cyber-input"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            
            <label htmlFor="flagInput" className="visually-hidden">Enter Flag</label>
            <input
              id="flagInput"
              type="text"
              className="cyber-input"
              placeholder="Enter flag (e.g., FLAG{...})"
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
            />
            
            <button
              className="cyber-button"
              onClick={checkFlag}
              disabled={isLoading}
            >
              {isLoading ? (
                <>Processing<span className="terminal-cursor"></span></>
              ) : (
                "Submit Flag"
              )}
            </button>
            
            {result && (
              <div className={`cyber-alert ${result.includes("✅") ? "success" : "error"}`}>
                {result}
              </div>
            )}
          </div>
          
          <div className="hint-section">
            {!showingHints ? (
              <button className="cyber-button" onClick={fetchHint}>
                Request Hint
              </button>
            ) : (
              <div className="cyber-card">
                <h3 className="cyber-section-header">Hint {currentHintIndex + 1}/{hints.length}</h3>
                <div className="terminal-text">
                  {hints[currentHintIndex]}
                </div>
                {currentHintIndex < hints.length - 1 && (
                  <button className="cyber-button" onClick={handleNextHint}>
                    Next Hint
                  </button>
                )}
              </div>
            )}
            
            {attempts >= MAX_ATTEMPTS && !showingSolution && (
              <button className="cyber-button" onClick={fetchSolution}>
                Show Solution
              </button>
            )}
            
            {showingSolution && (
              <div className="cyber-card">
                <h3 className="cyber-section-header">Solution</h3>
                <div className="terminal-text">
                  {solution}
                </div>
              </div>
            )}
          </div>
        </div>
        
        <button
          className="cyber-button"
          onClick={resetAndStartNew}
        >
          Start New Challenge
        </button>
      </div>
    );
  };

  const renderResult = () => {
    return (
      <div className="cyber-card fade-in">
        <h2 className="cyber-section-header">
          Challenge {result && result.includes("✅") ? "Completed" : "Failed"}
        </h2>
        
        <div className="terminal-text">
          {result}
        </div>
        
        {pointsEarned > 0 && (
          <div className="cyber-alert success">
            <div className="points-earned">
              <span className="glitch-text">+{pointsEarned} points</span> earned!
            </div>
            <div className="cyber-progress-container">
              <div 
                className="cyber-progress-bar" 
                style={{ width: `${Math.min(100, (totalPoints / 1000) * 100)}%` }}
              ></div>
            </div>
            <div className="total-points">
              Total: <span className="neon-text">{totalPoints}</span> points
            </div>
          </div>
        )}
        
        <div className="challenge-stats">
          <div className="hud-element">
            Category: <span className="neon-text">{challenge.category}</span>
          </div>
          <div className="hud-element">
            Difficulty: <span className="neon-text">{challenge.difficulty}</span>
          </div>
          <div className="hud-element">
            Attempts: <span className="neon-text">{attempts}/{MAX_ATTEMPTS}</span>
          </div>
        </div>
        
        {!showingSolution && (
          <button className="cyber-button" onClick={fetchSolution}>
            View Solution
          </button>
        )}
        
        {showingSolution && (
          <div className="cyber-card">
            <h3 className="cyber-section-header">Solution</h3>
            <div className="terminal-text">
              {solution}
            </div>
          </div>
        )}
        
        <button
          className="cyber-button"
          onClick={resetAndStartNew}
        >
          Start New Challenge
        </button>
        
        <button
          className="cyber-button"
          onClick={() => setActiveTab("stats")}
        >
          View Your Stats
        </button>
      </div>
    );
  };

  const renderAchievementPopup = () => {
    if (!showAchievementPopup || newAchievements.length === 0) return null;
    
    return (
      <div className="achievement-popup fade-in">
        <div className="cyber-card">
          <h3 className="cyber-section-header">Achievement Unlocked!</h3>
          {newAchievements.map((achievement, index) => (
            <div key={index} className="achievement-badge">
              <div className="achievement-icon">🏆</div>
              <div className="achievement-name">{achievement.name}</div>
              <div className="achievement-description">{achievement.description}</div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="cyber-container">
      {/* Header with tabs */}
      <div className="cyber-tabs">
        <div 
          className={`cyber-tab ${activeTab === "challenge" ? "active" : ""}`}
          onClick={() => setActiveTab("challenge")}
        >
          Challenges
        </div>
        {username && (
          <div 
            className={`cyber-tab ${activeTab === "stats" ? "active" : ""}`}
            onClick={() => setActiveTab("stats")}
          >
            Your Stats
          </div>
        )}
        {pointsEarned > 0 && (
          <div className="cyber-points">
            <span className="neon-text">{totalPoints}</span> points
          </div>
        )}
      </div>

      {/* Username Input */}
      {!username && (
        <div className="cyber-card fade-in">
          <h2 className="cyber-section-header">Enter Your Hacker Identity</h2>
          <input
            type="text"
            className="cyber-input"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter your username"
          />
          <div className="input-hint">
            Your username will be used to track your progress and achievements
          </div>
        </div>
      )}
      
      {/* Conditional rendering based on active tab */}
      {activeTab === "challenge" ? (
        /* Challenge Content */
        <>
          {/* Render appropriate UI based on current step */}
          {step === "difficulty" && renderDifficultySelection()}
          {step === "category" && renderCategorySelection()}
          {step === "challenge" && challenge && renderChallenge()}
          {step === "result" && renderResult()}
        </>
      ) : (
        /* Stats Content */
        <UserStats username={username} />
      )}
      
      {/* Achievement Popup */}
      {renderAchievementPopup()}
    </div>
  );
};

export default ChatInterface;
