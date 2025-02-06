import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown'; // Import Markdown renderer
import './App.css';

export function App() {
  const [userInput, setUserInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const sendMessage = async () => {
    if (!userInput.trim()) return;

    setMessages((prevMessages) => [
      ...prevMessages,
      { text: userInput, sender: 'user' },
    ]);
    setUserInput('');
    setLoading(true);

    try {
      const response = await axios.post('http://127.0.0.1:5000/chatbot', {
        question: userInput,
      });
      const botResponse = response.data.answer;

      setMessages((prevMessages) => [
        ...prevMessages,
        { text: botResponse, sender: 'bot' },
      ]);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div>
    <div className="chat-container">        
      <h1>Chatbot</h1>
      <div className="chat-box">
        <div className="messages">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.sender}`}>
              <ReactMarkdown>{msg.text}</ReactMarkdown> {/* Markdown support */}
            </div>
          ))}
          <div ref={messagesEndRef} />
          {loading && (
            <div className="message bot typing-indicator">
              <span>Typing...</span>
            </div>
          )}
        </div>
        <div className="input-container">
          <textarea
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            rows="2"
          />
          <button onClick={sendMessage} disabled={loading}>Send</button>
        </div>
      </div>
    </div>
    </div>
  );
}

export default App;
