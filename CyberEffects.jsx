import React, { useEffect, useRef } from 'react';
import './Cyber.css';

const CyberEffects = () => {
  const binaryBgRef = useRef(null);
  const particlesRef = useRef(null);
  const codeRainRef = useRef(null);

  // Create binary background
  useEffect(() => {
    if (!binaryBgRef.current) return;

    const binaryBg = binaryBgRef.current;
    binaryBg.innerHTML = '';

    const createBinaryDigit = () => {
      const digit = document.createElement('div');
      digit.className = 'binary-digit';
      digit.textContent = Math.random() > 0.5 ? '1' : '0';
      digit.style.left = `${Math.random() * 100}%`;
      digit.style.top = `${Math.random() * 100}%`;
      digit.style.opacity = Math.random() * 0.3;
      digit.style.animationDuration = `${3 + Math.random() * 5}s`;
      digit.style.animationDelay = `${Math.random() * 5}s`;
      return digit;
    };

    for (let i = 0; i < 200; i++) {
      binaryBg.appendChild(createBinaryDigit());
    }

    // Periodically add new digits
    const interval = setInterval(() => {
      if (binaryBg.children.length > 300) {
        for (let i = 0; i < 50; i++) {
          if (binaryBg.firstChild) {
            binaryBg.removeChild(binaryBg.firstChild);
          }
        }
      }
      for (let i = 0; i < 10; i++) {
        binaryBg.appendChild(createBinaryDigit());
      }
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  // Create floating particles
  useEffect(() => {
    if (!particlesRef.current) return;

    const particlesContainer = particlesRef.current;
    particlesContainer.innerHTML = '';

    const createParticle = () => {
      const particle = document.createElement('div');
      particle.className = 'particle';
      particle.style.left = `${Math.random() * 100}%`;
      particle.style.top = `${Math.random() * 100}%`;
      particle.style.width = `${2 + Math.random() * 3}px`;
      particle.style.height = particle.style.width;
      particle.style.opacity = 0.1 + Math.random() * 0.4;
      
      // Random color - mostly blue and green with occasional red for "threat" indication
      const colorRoll = Math.random();
      if (colorRoll > 0.9) {
        particle.style.backgroundColor = 'rgba(255, 0, 85, 0.7)'; // Red for threats
      } else if (colorRoll > 0.5) {
        particle.style.backgroundColor = 'rgba(0, 170, 255, 0.7)'; // Blue
      } else {
        particle.style.backgroundColor = 'rgba(0, 255, 157, 0.7)'; // Green
      }
      
      particle.style.animationDuration = `${15 + Math.random() * 30}s`;
      return particle;
    };

    for (let i = 0; i < 50; i++) {
      particlesContainer.appendChild(createParticle());
    }

    // Periodically add new particles
    const interval = setInterval(() => {
      if (particlesContainer.children.length > 80) {
        if (particlesContainer.firstChild) {
          particlesContainer.removeChild(particlesContainer.firstChild);
        }
      }
      particlesContainer.appendChild(createParticle());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Create Matrix-like code rain effect
  useEffect(() => {
    if (!codeRainRef.current) return;

    const codeRainContainer = codeRainRef.current;
    codeRainContainer.innerHTML = '';

    const chars = '01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン';
    
    const createCodeColumn = () => {
      const column = document.createElement('div');
      column.className = 'code-column';
      column.style.left = `${Math.random() * 100}%`;
      column.style.animationDuration = `${5 + Math.random() * 15}s`;
      
      const length = 10 + Math.floor(Math.random() * 20);
      let content = '';
      
      for (let i = 0; i < length; i++) {
        content += chars.charAt(Math.floor(Math.random() * chars.length)) + '<br>';
      }
      
      column.innerHTML = content;
      return column;
    };

    for (let i = 0; i < 20; i++) {
      codeRainContainer.appendChild(createCodeColumn());
    }

    // Periodically add new code columns
    const interval = setInterval(() => {
      if (codeRainContainer.children.length > 30) {
        if (codeRainContainer.firstChild) {
          codeRainContainer.removeChild(codeRainContainer.firstChild);
        }
      }
      codeRainContainer.appendChild(createCodeColumn());
    }, 800);

    return () => clearInterval(interval);
  }, []);

  // HUD elements that follow cursor
  useEffect(() => {
    const handleMouseMove = (e) => {
      const hudElements = document.querySelectorAll('.hud-tracker');
      hudElements.forEach((element) => {
        const rect = element.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        element.style.setProperty('--mouse-x', `${x}px`);
        element.style.setProperty('--mouse-y', `${y}px`);
      });
    };

    document.addEventListener('mousemove', handleMouseMove);
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  // Scanning animation for page
  useEffect(() => {
    const scan = () => {
      const scanLine = document.createElement('div');
      scanLine.className = 'scan-line';
      scanLine.style.position = 'fixed';
      scanLine.style.top = '0';
      scanLine.style.left = '0';
      scanLine.style.width = '100%';
      scanLine.style.height = '2px';
      scanLine.style.backgroundColor = 'rgba(0, 255, 157, 0.7)';
      scanLine.style.boxShadow = '0 0 10px rgba(0, 255, 157, 0.7)';
      scanLine.style.zIndex = '1000';
      scanLine.style.pointerEvents = 'none';
      scanLine.style.transform = 'translateY(0)';
      scanLine.style.transition = 'transform 1.5s linear';
      
      document.body.appendChild(scanLine);
      
      // Animate scan line
      setTimeout(() => {
        scanLine.style.transform = 'translateY(100vh)';
      }, 100);
      
      // Remove scan line after animation
      setTimeout(() => {
        if (document.body.contains(scanLine)) {
          document.body.removeChild(scanLine);
        }
      }, 1600);
    };

    // Initial scan
    scan();
    
    // Periodic scan
    const interval = setInterval(scan, 30000);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <div ref={binaryBgRef} className="binary-bg"></div>
      <div ref={particlesRef} className="particles-container"></div>
      <div ref={codeRainRef} className="code-rain"></div>
    </>
  );
};

export default CyberEffects; 