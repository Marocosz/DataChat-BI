// =================================================================================================
// =================================================================================================
//
//                         COMPONENTE DA PÁGINA PRINCIPAL DE CHAT
//
// Visão Geral do Componente:
//
// Este arquivo define o componente `Chat`, que funciona como o "container" inteligente para
// toda a interface de conversação. Ele é responsável por gerenciar o estado da aplicação,
// lidar com a interação do usuário e orquestrar a comunicação com o backend.
//
// Principais Responsabilidades:
//
// 1. Gerenciamento de Estado (`useState`):
//    - `messages`: Mantém um array com todo o histórico da conversa exibido na tela.
//    - `input`: Controla o valor atual do campo de texto onde o usuário digita.
//    - `isLoading`: Gerencia a exibição do indicador de "carregando" enquanto espera
//      a resposta do backend.
//    - `sessionId`: Armazena o ID único da sessão de chat, garantindo que o backend
//      possa rastrear o contexto da conversa.
//
// 2. Lógica de Ciclo de Vida (`useEffect`):
//    - Na primeira renderização, gera um `sessionId` único que persiste por toda a conversa.
//    - A cada nova mensagem, rola a janela de chat para o final para manter a visibilidade.
//
// 3. Comunicação com a API (`axios`):
//    - No envio da mensagem, formata e envia a pergunta do usuário junto com o `sessionId`
//      para o endpoint `/chat` do backend.
//    - Processa a resposta do backend ou trata possíveis erros de comunicação.
//
// 4. Renderização da UI:
//    - Mapeia o array de `messages` para renderizar uma lista de componentes `ChatMessage`.
//    - Exibe o formulário de entrada de texto e o botão de envio.
//
// =================================================================================================
// =================================================================================================

import React, { useState, useEffect, useRef } from 'react';
// Biblioteca para realizar as chamadas HTTP para o backend.
import axios from 'axios';
// Biblioteca para gerar identificadores únicos universais (UUIDs) para as sessões.
import { v4 as uuidv4 } from 'uuid'; 
// Importa o componente filho que renderiza cada mensagem individual.
import ChatMessage from '../components/ChatMessage';
// Importa o ícone de envio.
import { FiSend } from 'react-icons/fi';
// Importa a folha de estilos da página de chat.
import './Chat.css';

function Chat() {
  // --- GERENCIAMENTO DE ESTADO (useState) ---

  // Armazena todas as mensagens da conversa (inicia com uma saudação do bot).
  const [messages, setMessages] = useState([
    { sender: 'bot', content: { type: 'text', content: 'Olá! Como posso ajudar com os dados de logística hoje?' } }
  ]);
  // Armazena o texto atual do campo de input do usuário.
  const [input, setInput] = useState('');
  // Controla se a aplicação está aguardando uma resposta do backend.
  const [isLoading, setIsLoading] = useState(false);
  // Armazena o ID único para toda a sessão de chat.
  const [sessionId, setSessionId] = useState(null);

  // --- REFERÊNCIAS E EFEITOS DE CICLO DE VIDA (useRef, useEffect) ---

  // Cria uma referência direta ao elemento DOM da janela de chat para controlar o scroll.
  const chatWindowRef = useRef(null);
  
  // Efeito que roda UMA VEZ quando o componente é montado pela primeira vez.
  useEffect(() => {
    // Gera um novo ID de sessão único e o armazena no state para ser usado em todas as requisições.
    setSessionId(uuidv4());
  }, []); // O array de dependências vazio `[]` garante que esta função execute apenas no "mount".

  // Efeito que roda TODA VEZ que o array `messages` é atualizado.
  useEffect(() => {
    // Se a referência à janela de chat existir, rola a tela para o final.
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages]);

  // --- MANIPULADORES DE EVENTOS ---

  // Função assíncrona para lidar com o envio da mensagem pelo usuário.
  const handleSubmit = async (e) => {
    e.preventDefault(); // Previne o recarregamento da página, comportamento padrão de formulários.
    // Impede o envio se o input estiver vazio, se já houver uma requisição em andamento, ou se o ID da sessão ainda não foi gerado.
    if (!input.trim() || isLoading || !sessionId) return; 

    // Cria o objeto da mensagem do usuário e o adiciona ao estado para feedback visual imediato.
    const userMessage = { sender: 'user', content: { type: 'text', content: input } };
    setMessages((prev) => [...prev, userMessage]);
    
    // Limpa o campo de input e ativa o estado de carregamento.
    setInput('');
    setIsLoading(true);

    try {
      // Envia a requisição POST para o backend, incluindo a pergunta e o ID da sessão.
      const response = await axios.post('http://localhost:8000/chat', { 
        question: input,
        session_id: sessionId 
      });
      // Cria o objeto da mensagem do bot com os dados recebidos da API.
      const botMessage = { sender: 'bot', content: response.data };
      // Adiciona a resposta do bot ao estado de mensagens.
      setMessages((prev) => [...prev, botMessage]);

    } catch (error) {
      // Em caso de erro na comunicação com a API, loga o erro e exibe uma mensagem amigável.
      console.error("Error fetching bot response:", error);
      const errorMessage = { sender: 'bot', content: { type: 'text', content: 'Desculpe, não consegui me conectar ao servidor.' } };
      setMessages((prev) => [...prev, errorMessage]);

    } finally {
      // Este bloco é executado independentemente de sucesso ou falha na requisição.
      // Desativa o estado de carregamento, liberando o input para o usuário novamente.
      setIsLoading(false);
    }
  };

  // --- RENDERIZAÇÃO DO COMPONENTE ---

  return (
    <div className="chat-container">
      {/* A janela de chat onde as mensagens são exibidas. A `ref` conecta este div ao `chatWindowRef`. */}
      <div className="chat-window" ref={chatWindowRef}>
        {/* Mapeia o array de mensagens, renderizando um componente `ChatMessage` para cada item. */}
        {messages.map((msg, index) => (
          <ChatMessage key={index} sender={msg.sender} content={msg.content} />
        ))}
        {/* Renderiza o indicador de "digitando..." apenas se `isLoading` for verdadeiro. */}
        {isLoading && (
          <div className="message-wrapper bot-wrapper">
              <div className="message bot-message">
                <div className="loading-dots"><div></div><div></div><div></div></div>
              </div>
          </div>
        )}
      </div>

      {/* Área do formulário de entrada de texto. */}
      <div className="chat-input-area">
        <form onSubmit={handleSubmit} className="chat-input-form">
          <input
            type="text"
            value={input} // O valor do input é controlado pelo state `input`.
            onChange={(e) => setInput(e.target.value)} // Atualiza o state a cada letra digitada.
            placeholder="Pergunte algo sobre os dados..."
            disabled={isLoading} // Desabilita o input enquanto aguarda a resposta.
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