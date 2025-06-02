import React, { useState, useEffect } from "react";
import axios from "axios";

const ProgressTracker = () => {
  const [progress, setProgress] = useState([]);
  const [userId, setUserId] = useState(() => {
    return localStorage.getItem("user_id") || `guest_${Math.random().toString(36).substr(2, 9)}`;
  });

  useEffect(() => {
    localStorage.setItem("user_id", userId);
  }, [userId]);

  useEffect(() => {
    fetchProgress();
  }, [userId]);

  const fetchProgress = async () => {
    try {
      const response = await axios.get("http://localhost:5000/get_progress", {
        params: { user_id: userId },
      });
      setProgress(response.data.progress);
    } catch (error) {
      console.error("Error fetching progress", error);
    }
  };

  return (
    <div>
      <h2>Progress Tracker</h2>
      {progress.length > 0 ? (
        <ul>
          {progress.map((stat, index) => (
            <li key={index}>
              <strong>Category:</strong> {stat.category} | 
              <strong> Attempts:</strong> {stat.total_attempts} | 
              <strong> Correct:</strong> {stat.correct_attempts} | 
              <strong> Avg Time:</strong> {stat.avg_time.toFixed(2)}s
            </li>
          ))}
        </ul>
      ) : (
        <p>Loading progress...</p>
      )}
    </div>
  );
};

export default ProgressTracker;
