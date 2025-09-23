import React from 'react';
import ChartComponent from './ChartComponent';
import { FiUser, FiCpu } from 'react-icons/fi';
import './ChatMessage.css';

const ChatMessage = ({ sender, content }) => {
  const isBot = sender === 'bot';
  const Avatar = isBot ? FiCpu : FiUser;

  // --- LÓGICA DE CLASSES ATUALIZADA ---
  let messageClasses = `message ${isBot ? 'bot-message' : 'user-message'}`;
  let wrapperClasses = `message-wrapper ${isBot ? 'bot-wrapper' : 'user-wrapper'}`;
  
  if (content.type === 'chart') {
    messageClasses += ' has-chart';
    wrapperClasses += ' wrapper-has-chart'; // Adiciona classe ao wrapper também
  }
  // ------------------------------------

  const renderContent = () => {
    if (content.type === 'chart') {
      return <ChartComponent chartData={content} />;
    }
    return <p>{content.content}</p>;
  };

  return (
    // Usa a nova variável de classes para o wrapper
    <div className={wrapperClasses}>
      <div className="avatar">
        <Avatar />
      </div>
      <div className={messageClasses}>
        {renderContent()}
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