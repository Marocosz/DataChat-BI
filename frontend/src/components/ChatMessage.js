import React from 'react';
import ChartComponent from './ChartComponent';
import { FiUser, FiCpu } from 'react-icons/fi'; // Ícones para os avatares
import './ChatMessage.css';

// --- COMPONENTE DE MENSAGEM INDIVIDUAL DO CHAT ---

const ChatMessage = ({ sender, content }) => {
  // Determina se a mensagem é do bot para aplicar estilos e ícones diferentes.
  const isBot = sender === 'bot';
  // Escolhe o ícone do avatar com base em quem enviou a mensagem.
  const Avatar = isBot ? FiCpu : FiUser;

  // Função interna para decidir qual tipo de conteúdo renderizar (texto ou gráfico).
  const renderContent = () => {
    if (content.type === 'chart') {
      return <ChartComponent chartData={content} />;
    }
    // O padrão é sempre renderizar o conteúdo de texto.
    return <p>{content.content}</p>;
  };

  // A estrutura JSX agora inclui um wrapper principal para alinhar a mensagem
  // e o avatar corretamente (esquerda para o bot, direita para o usuário).
  return (
    <div className={`message-wrapper ${isBot ? 'bot-wrapper' : 'user-wrapper'}`}>
      <div className="avatar">
        <Avatar />
      </div>
      <div className={`message ${isBot ? 'bot-message' : 'user-message'}`}>
        {renderContent()}
        
        {/* Renderiza o tempo de resposta apenas se for uma mensagem do bot e se a informação existir */}
        {isBot && content.response_time && (
          <div className="response-time-meta">
            <span>Gerado em {content.response_time}s</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;