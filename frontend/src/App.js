import React, { useState } from 'react';
import axios from 'axios';
import ChatMessage from './ChatMessage';
import './App.css';

function App() {
  const [messages, setMessages] = useState([
    { sender: 'bot', content: { type: 'text', content: 'Olá! Como posso ajudar com os dados de logística hoje?' } }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { sender: 'user', content: { type: 'text', content: input } };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/chat', { question: input });
      const botMessage = { sender: 'bot', content: response.data };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error fetching bot response:", error);
      const errorMessage = { sender: 'bot', content: { type: 'text', content: 'Desculpe, não consegui me conectar ao servidor.' } };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>SuppBot Logística 📊</h1>
      </header>
      <div className="chat-window">
        {messages.map((msg, index) => (
          <ChatMessage key={index} sender={msg.sender} content={msg.content} />
        ))}
        {isLoading && <div className="message bot-message"><div className="loading-dots"><div></div><div></div><div></div></div></div>}
      </div>
      <form onSubmit={handleSubmit} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Qual o valor de frete por estado?"
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading}>Enviar</button>
      </form>
    </div>
  );
}

export default App;