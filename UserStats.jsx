import React, { useState, useEffect } from "react";
import axios from "axios";

const API_BASE_URL = "http://localhost:5000";

const UserStats = ({ username }) => {
  const [userStats, setUserStats] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (username) {
      fetchData();
    }
  }, [username]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      await Promise.all([
        fetchUserStats(),
        fetchLeaderboard()
      ]);
    } catch (error) {
      console.error("Error fetching data:", error);
      setError("Failed to load data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const fetchUserStats = async () => {
    try {
      console.log(`Fetching stats for user: ${username}`);
      const response = await axios.get(`${API_BASE_URL}/user_stats/${username}`);
      console.log("User stats response:", response.data);
      setUserStats(response.data);
    } catch (error) {
      console.error("Error fetching user stats:", error);
      throw error;
    }
  };

  const fetchLeaderboard = async () => {
    try {
      console.log("Fetching leaderboard");
      const response = await axios.get(`${API_BASE_URL}/leaderboard`);
      console.log("Leaderboard response:", response.data);
      setLeaderboard(response.data || []);
    } catch (error) {
      console.error("Error fetching leaderboard:", error);
      throw error;
    }
  };

  const formatTime = (seconds) => {
    if (!seconds) return "N/A";
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    if (minutes === 0) {
      return `${remainingSeconds}s`;
    }
    
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return "N/A";
    
    try {
      const date = new Date(timestamp * 1000); // Convert Unix timestamp to JS date
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    } catch (e) {
      console.error("Error formatting date:", e);
      return "N/A";
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "50px 0" }}>
        <div style={{ fontSize: "24px", marginBottom: "20px" }}>Loading stats...</div>
        <div style={{ 
          width: "50px", 
          height: "50px", 
          border: "5px solid #f3f3f3", 
          borderTop: "5px solid #3498db", 
          borderRadius: "50%", 
          margin: "auto",
          animation: "spin 1s linear infinite"
        }}></div>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        backgroundColor: "#ffdddd", 
        color: "#d8000c", 
        padding: "20px", 
        borderRadius: "5px", 
        textAlign: "center" 
      }}>
        <div style={{ fontSize: "20px", marginBottom: "10px" }}>Error</div>
        <div>{error}</div>
        <button 
          onClick={fetchData} 
          style={{ 
            backgroundColor: "#4CAF50", 
            border: "none", 
            color: "white", 
            padding: "10px 15px", 
            textAlign: "center", 
            borderRadius: "5px", 
            marginTop: "15px", 
            cursor: "pointer" 
          }}
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!userStats) {
    return (
      <div style={{ textAlign: "center", padding: "20px" }}>
        <div style={{ fontSize: "20px", marginBottom: "10px" }}>No stats available</div>
        <div>Complete some challenges to see your stats!</div>
      </div>
    );
  }

  const userRank = leaderboard.findIndex(user => 
    user.username === username || user.user_id === username
  ) + 1;

  return (
    <div style={{ fontFamily: 'Arial, sans-serif' }}>
      <div style={{ 
        display: "flex", 
        justifyContent: "space-between", 
        alignItems: "center",
        marginBottom: "20px"
      }}>
        <h2 style={{ margin: 0 }}>Performance Dashboard</h2>
        <button 
          onClick={fetchData} 
          style={{ 
            backgroundColor: "#4CAF50", 
            border: "none", 
            color: "white", 
            padding: "8px 15px", 
            textAlign: "center", 
            borderRadius: "5px", 
            cursor: "pointer" 
          }}
        >
          Refresh
        </button>
      </div>

      {/* Main layout - two column grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        {/* Left column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* Summary Card */}
          <div style={{ 
            backgroundColor: "#1a1a2e", 
            color: "white", 
            padding: "20px", 
            borderRadius: "10px",
            boxShadow: "0 4px 8px rgba(0,0,0,0.1)"
          }}>
            <h3 style={{ marginTop: 0 }}>Summary</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "15px" }}>
              <div>
                <div style={{ fontSize: "14px", color: "#aaa" }}>Points</div>
                <div style={{ fontSize: "28px", fontWeight: "bold" }}>{userStats.total_points || 0}</div>
              </div>
              <div>
                <div style={{ fontSize: "14px", color: "#aaa" }}>Rank</div>
                <div style={{ fontSize: "28px", fontWeight: "bold" }}>{userRank > 0 ? `#${userRank}` : "N/A"}</div>
              </div>
              <div>
                <div style={{ fontSize: "14px", color: "#aaa" }}>Challenges Completed</div>
                <div style={{ fontSize: "28px", fontWeight: "bold" }}>{userStats.challenges_completed || 0}</div>
              </div>
              <div>
                <div style={{ fontSize: "14px", color: "#aaa" }}>Fastest Solve</div>
                <div style={{ fontSize: "28px", fontWeight: "bold" }}>{formatTime(userStats.fastest_solve)}</div>
              </div>
            </div>
          </div>

          {/* Progress by Difficulty */}
          <div style={{ 
            backgroundColor: "white", 
            padding: "20px", 
            borderRadius: "10px",
            boxShadow: "0 4px 8px rgba(0,0,0,0.1)"
          }}>
            <h3 style={{ marginTop: 0 }}>Progress by Difficulty</h3>
            <div style={{ display: "flex", gap: "10px", marginTop: "15px" }}>
              {Object.entries(userStats.difficulty_count || {}).map(([difficulty, count]) => (
                <div 
                  key={difficulty}
                  style={{
                    flex: 1,
                    backgroundColor: 
                      difficulty === "Easy" ? "#4caf5020" : 
                      difficulty === "Medium" ? "#ff980020" :
                      difficulty === "Hard" ? "#f4433620" : "#e0e0e020",
                    padding: "15px",
                    borderRadius: "8px",
                    textAlign: "center"
                  }}
                >
                  <div style={{ 
                    color: 
                      difficulty === "Easy" ? "#4caf50" : 
                      difficulty === "Medium" ? "#ff9800" :
                      difficulty === "Hard" ? "#f44336" : "#757575",
                    fontWeight: "bold",
                    fontSize: "20px"
                  }}>
                    {count}
                  </div>
                  <div style={{ fontSize: "14px", marginTop: "5px" }}>{difficulty}</div>
                </div>
              ))}
              {Object.keys(userStats.difficulty_count || {}).length === 0 && (
                <div style={{ padding: "15px", color: "#757575", textAlign: "center", width: "100%" }}>
                  No challenges completed yet
                </div>
              )}
            </div>
          </div>

          {/* Achievements */}
          <div style={{ 
            backgroundColor: "white", 
            padding: "20px", 
            borderRadius: "10px",
            boxShadow: "0 4px 8px rgba(0,0,0,0.1)"
          }}>
            <h3 style={{ marginTop: 0 }}>Achievements</h3>
            {userStats.achievements && userStats.achievements.length > 0 ? (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: "15px" }}>
                {userStats.achievements.map((achievement, index) => (
                  <div 
                    key={index}
                    style={{
                      backgroundColor: "#f5f5f5",
                      borderRadius: "8px",
                      padding: "15px",
                      textAlign: "center"
                    }}
                  >
                    <div style={{ fontSize: "32px", marginBottom: "10px" }}>{achievement.icon}</div>
                    <div style={{ fontWeight: "bold", marginBottom: "5px" }}>{achievement.name}</div>
                    <div style={{ fontSize: "12px", color: "#666" }}>{achievement.description}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ padding: "15px", color: "#757575", textAlign: "center" }}>
                No achievements unlocked yet
              </div>
            )}
          </div>
        </div>

        {/* Right column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* Category Mastery */}
          <div style={{ 
            backgroundColor: "white", 
            padding: "20px", 
            borderRadius: "10px",
            boxShadow: "0 4px 8px rgba(0,0,0,0.1)"
          }}>
            <h3 style={{ marginTop: 0 }}>Category Mastery</h3>
            {Object.entries(userStats.category_count || {}).length > 0 ? (
              <div>
                {Object.entries(userStats.category_count).map(([category, count]) => (
                  <div 
                    key={category}
                    style={{ 
                      display: "flex", 
                      justifyContent: "space-between", 
                      alignItems: "center",
                      padding: "10px 0",
                      borderBottom: "1px solid #f0f0f0"
                    }}
                  >
                    <div>{category}</div>
                    <div style={{ 
                      backgroundColor: "#1a1a2e", 
                      color: "white", 
                      padding: "5px 10px", 
                      borderRadius: "15px",
                      fontSize: "14px"
                    }}>
                      {count} solved
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ padding: "15px", color: "#757575", textAlign: "center" }}>
                No challenges completed yet
              </div>
            )}
          </div>

          {/* Leaderboard */}
          <div style={{ 
            backgroundColor: "white", 
            padding: "20px", 
            borderRadius: "10px",
            boxShadow: "0 4px 8px rgba(0,0,0,0.1)"
          }}>
            <h3 style={{ marginTop: 0 }}>Leaderboard</h3>
            {leaderboard.length > 0 ? (
              <div>
                {leaderboard.map((user, index) => (
                  <div 
                    key={index}
                    style={{ 
                      display: "flex", 
                      justifyContent: "space-between", 
                      alignItems: "center",
                      padding: "10px",
                      backgroundColor: user.username === username || user.user_id === username ? "#f0f7ff" : "transparent",
                      borderRadius: "5px",
                      marginBottom: "5px",
                      fontWeight: user.username === username || user.user_id === username ? "bold" : "normal"
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <div style={{ 
                        width: "25px", 
                        height: "25px", 
                        backgroundColor: 
                          index === 0 ? "#ffd700" : 
                          index === 1 ? "#c0c0c0" : 
                          index === 2 ? "#cd7f32" : "#e0e0e0",
                        borderRadius: "50%",
                        display: "flex",
                        justifyContent: "center",
                        alignItems: "center",
                        color: index <= 2 ? "white" : "#333"
                      }}>
                        {user.rank}
                      </div>
                      <div>{user.username}</div>
                    </div>
                    <div style={{ display: "flex", gap: "15px" }}>
                      <div>
                        <span style={{ color: "#666", fontSize: "12px", marginRight: "5px" }}>Points:</span>
                        <span style={{ fontWeight: "bold" }}>{user.points}</span>
                      </div>
                      <div>
                        <span style={{ color: "#666", fontSize: "12px", marginRight: "5px" }}>Solved:</span>
                        <span>{user.challenges_completed}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ padding: "15px", color: "#757575", textAlign: "center" }}>
                No data available
              </div>
            )}
          </div>

          {/* Recent Activity */}
          <div style={{ 
            backgroundColor: "white", 
            padding: "20px", 
            borderRadius: "10px",
            boxShadow: "0 4px 8px rgba(0,0,0,0.1)"
          }}>
            <h3 style={{ marginTop: 0 }}>Recent Activity</h3>
            {userStats.recent_activity && userStats.recent_activity.length > 0 ? (
              <div>
                {userStats.recent_activity.map((activity, index) => (
                  <div 
                    key={index}
                    style={{ 
                      display: "flex", 
                      justifyContent: "space-between", 
                      alignItems: "center",
                      padding: "10px 0",
                      borderBottom: index < userStats.recent_activity.length - 1 ? "1px solid #f0f0f0" : "none"
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: "bold" }}>{activity.challenge}</div>
                      <div style={{ fontSize: "12px", color: "#666" }}>
                        {activity.category} - {activity.difficulty}
                      </div>
                      <div style={{ fontSize: "11px", color: "#999", marginTop: "3px" }}>
                        {formatDate(activity.timestamp)}
                      </div>
                    </div>
                    <div style={{ 
                      backgroundColor: activity.completed ? "#4caf5020" : "#f4433620", 
                      color: activity.completed ? "#4caf50" : "#f44336", 
                      padding: "5px 10px", 
                      borderRadius: "15px",
                      fontSize: "12px",
                      fontWeight: "bold"
                    }}>
                      {activity.completed ? "COMPLETED" : "FAILED"}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ padding: "15px", color: "#757575", textAlign: "center" }}>
                No recent activity
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserStats; 