import React from 'react';
import ChartComponent from './ChartComponent';
import { FiUser, FiCpu } from 'react-icons/fi';
import './ChatMessage.css';

const ChatMessage = ({ sender, content }) => {
  const isBot = sender === 'bot';
  const Avatar = isBot ? FiCpu : FiUser;

  // Lógica para adicionar a classe .has-chart dinamicamente
  let messageClasses = `message ${isBot ? 'bot-message' : 'user-message'}`;
  if (content.type === 'chart') {
    messageClasses += ' has-chart';
  }

  const renderContent = () => {
    if (content.type === 'chart') {
      return <ChartComponent chartData={content} />;
    }
    return <p>{content.content}</p>;
  };

  return (
    <div className={`message-wrapper ${isBot ? 'bot-wrapper' : 'user-wrapper'}`}>
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