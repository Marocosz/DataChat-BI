import React, { useState } from 'react'; // 1. Importar useState
import ChartComponent from './ChartComponent';
// 2. Importar os ícones necessários
import { FiUser, FiCpu, FiChevronDown, FiCode } from 'react-icons/fi'; 
import './ChatMessage.css';

const ChatMessage = ({ sender, content }) => {
  const isBot = sender === 'bot';
  const Avatar = isBot ? FiCpu : FiUser;

  // =============================================================================
  // ## INÍCIO DA ATUALIZAÇÃO ##
  // =============================================================================

  // 3. Adicionar um estado para controlar se a query está visível ou não
  const [isQueryVisible, setIsQueryVisible] = useState(false);

  // 4. Verificar se a mensagem do bot possui uma query para ser exibida
  const hasQuery = isBot && content.generated_sql;

  // 5. Função para alternar a visibilidade da query
  const toggleQueryVisibility = () => {
    setIsQueryVisible(!isQueryVisible);
  };

  // =============================================================================
  // ## FIM DA ATUALIZAÇÃO ##
  // =============================================================================

  let messageClasses = `message ${isBot ? 'bot-message' : 'user-message'}`;
  let wrapperClasses = `message-wrapper ${isBot ? 'bot-wrapper' : 'user-wrapper'}`;
  
  if (content.type === 'chart') {
    messageClasses += ' has-chart';
    wrapperClasses += ' wrapper-has-chart';
  }

  const renderContent = () => {
    if (content.type === 'chart') {
      return <ChartComponent chartData={content} />;
    }
    return <p>{content.content}</p>;
  };

  return (
    <div className={wrapperClasses}>
      <div className="avatar">
        <Avatar />
      </div>
      <div className={messageClasses}>
        {renderContent()}

        {/* ============================================================================= */}
        {/* ## INÍCIO DA ATUALIZAÇÃO ## */}
        {/* ============================================================================= */}

        {/* 6. Adiciona um "rodapé" na mensagem do bot para alinhar tempo de resposta e o botão da query */}
        {isBot && (
          <div className="message-footer">
            {/* O tempo de resposta continua aqui */}
            {content.response_time && (
              <div className="response-time-meta">
                <span>Gerado em {content.response_time}s</span>
              </div>
            )}

            {/* O botão para mostrar/ocultar a query só aparece se houver uma query */}
            {hasQuery && (
              <button className="query-toggle-button" onClick={toggleQueryVisibility}>
                <FiCode size={14} /> 
                <span>Ver Query</span>
                <FiChevronDown size={14} className={`query-toggle-arrow ${isQueryVisible ? 'toggled' : ''}`} />
              </button>
            )}
          </div>
        )}
        
        {/* 7. A caixa com o código da query só é renderizada se hasQuery e isQueryVisible forem verdadeiros */}
        {hasQuery && isQueryVisible && (
          <div className="query-display">
            <pre><code>{content.generated_sql}</code></pre>
          </div>
        )}

        {/* ============================================================================= */}
        {/* ## FIM DA ATUALIZAÇÃO ## */}
        {/* ============================================================================= */}
      </div>
    </div>
  );
};

export default ChatMessage;