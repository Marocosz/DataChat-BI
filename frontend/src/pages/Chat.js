import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
// =============================================================================
// ## INÍCIO DA ATUALIZAÇÃO ##
// =============================================================================
// 1. Importar a função para gerar UUIDs
import { v4 as uuidv4 } from 'uuid'; 
// =============================================================================
// ## FIM DA ATUALIZAÇÃO ##
// =============================================================================
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
  
  // =============================================================================
  // ## INÍCIO DA ATUALIZAÇÃO ##
  // =============================================================================
  // 2. Adicionar um state para armazenar o ID da sessão de chat
  const [sessionId, setSessionId] = useState(null);
  // =============================================================================
  // ## FIM DA ATUALIZAÇÃO ##
  // =============================================================================

  // Ref para a div da janela de chat, para controlar o scroll
  const chatWindowRef = useRef(null);
  
  // =============================================================================
  // ## INÍCIO DA ATUALIZAÇÃO ##
  // =============================================================================
  // 3. Adicionar um useEffect para gerar o ID da sessão UMA VEZ quando o componente é montado
  useEffect(() => {
    // Gera um novo ID de sessão único e o armazena no state
    setSessionId(uuidv4());
  }, []); // O array de dependências vazio `[]` garante que isso rode apenas uma vez
  // =============================================================================
  // ## FIM DA ATUALIZAÇÃO ##
  // =============================================================================

  // Efeito para rolar a janela de chat para baixo sempre que uma nova mensagem é adicionada
  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages]);

  // Função para lidar com o envio do formulário
  const handleSubmit = async (e) => {
    e.preventDefault();
    // 4. Adiciona uma verificação para garantir que temos um sessionId antes de enviar
    if (!input.trim() || isLoading || !sessionId) return; 

    const userMessage = { sender: 'user', content: { type: 'text', content: input } };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // 5. Envia o `question` E o `session_id` para o backend
      const response = await axios.post('http://localhost:8000/chat', { 
        question: input,
        session_id: sessionId // <--- A MUDANÇA CRÍTICA ESTÁ AQUI
      });
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