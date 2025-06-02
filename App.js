import React from "react";
import ChatInterface from "./components/ChatInterface";
import ProgressTracker from "./components/ProgressTracker";
import CyberEffects from "./components/CyberEffects";
import "./components/Cyber.css";

function App() {
  return (
    <div className="cyber-app">
      <CyberEffects />
      <div className="cyber-container">
        <header className="cyber-header">
          <h1 className="glitch-text">CyberSensei:CTF AI Trainer</h1>
        </header>
        <main className="cyber-content fade-in">
          <ChatInterface />
          <div className="cyber-scanner">
            <ProgressTracker />
          </div>
        </main>
        <footer className="cyber-footer">
          <div className="hud-element">System Status: <span className="neon-text">Online</span></div>
        </footer>
      </div>
    </div>
  );
}

export default App;
