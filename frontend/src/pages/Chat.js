import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ChatMessage from '../components/ChatMessage';
import { FiSend } from 'react-icons/fi';
import './Chat.css';

// --- COMPONENTE DA PÁGINA DE CHAT ---

function Chat() {
  // State para armazenar o histórico de mensagens
  const [messages, setMessages] = useState([
    { sender: 'bot', content: { type: 'text', content: 'Olá! Como posso ajudar com os dados de logística hoje?' } }
  ]);
  // State para controlar o valor do campo de input
  const [input, setInput] = useState('');
  // State para mostrar o indicador de "carregando" enquanto o bot responde
  const [isLoading, setIsLoading] = useState(false);
  
  // Ref para a div da janela de chat, para controlar o scroll
  const chatWindowRef = useRef(null);

  // Efeito para rolar a janela de chat para baixo sempre que uma nova mensagem é adicionada
  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages]);

  // Função para lidar com o envio do formulário
  const handleSubmit = async (e) => {
    e.preventDefault(); // Previne o comportamento padrão de recarregar a página
    if (!input.trim() || isLoading) return; // Não envia se o input estiver vazio ou se já estiver carregando

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
      setIsLoading(false); // Para de carregar, independentemente do resultado
    }
  };

  return (
    <div className="chat-container">
      {/* A janela de chat onde as mensagens são exibidas */}
      <div className="chat-window" ref={chatWindowRef}>
        {messages.map((msg, index) => (
          <ChatMessage key={index} sender={msg.sender} content={msg.content} />
        ))}
        {/* Mostra o indicador de "digitando" quando isLoading é true */}
        {isLoading && (
          <div className="message-wrapper bot-wrapper">
             <div className="message bot-message">
               <div className="loading-dots"><div></div><div></div><div></div></div>
             </div>
          </div>
        )}
      </div>

      {/* Formulário para o usuário digitar e enviar a mensagem */}
      <div className="chat-input-area">
        <form onSubmit={handleSubmit} className="chat-input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Pergunte algo sobre os dados..."
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading}>
            <FiSend />
          </button>
        </form>
      </div>
    </div>
  );
}

export default Chat;