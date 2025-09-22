import React from 'react';
import ChartComponent from './ChartComponent';
import './ChatMessage.css';

const ChatMessage = ({ sender, content }) => {
  const isBot = sender === 'bot';

  const renderContent = () => {
    if (content.type === 'chart') {
      return <ChartComponent chartData={content} />;
    }
    return <p>{content.content}</p>;
  };

  return (
    <div className={`message-wrapper ${isBot ? 'bot-wrapper' : 'user-wrapper'}`}>
      <div className={`message ${isBot ? 'bot-message' : 'user-message'}`}>
        {renderContent()}
      </div>
    </div>
  );
};

export default ChatMessage;