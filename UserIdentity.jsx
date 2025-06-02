import React, { useState } from 'react';

const UserIdentity = () => {
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');

  const handleUsernameChange = (e) => {
    setUsername(e.target.value);
  };

  const validateUsername = () => {
    if (!username || username.trim() === '') {
      setError("Username is required");
      return false;
    }
    
    if (username.length < 2) {
      setError("Username must be at least 2 characters");
      return false;
    }
    
    if (username.length > 20) {
      setError("Username must be less than 20 characters");
      return false;
    }
    
    // Additional validation like no special characters if needed
    return true;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validateUsername()) {
      // Proceed with submission
      onSubmitUsername(username.trim());
    }
  };

  return (
    <input
      type="text"
      value={username}
      onChange={handleUsernameChange}
      placeholder="Enter your hacker identity"
      className="cyber-input"
      maxLength="20"
      minLength="2"
    />
  );
};

export default UserIdentity; 