// =================================================================================================
// =================================================================================================
//
//                     COMPONENTE DE EXIBIÇÃO DE MENSAGEM DO CHAT
//
// Visão Geral do Componente:
//
// Este arquivo define o componente React `ChatMessage`, que é responsável por renderizar
// uma única mensagem dentro da janela de chat. Ele foi projetado para ser flexível e
// inteligente, adaptando sua aparência e funcionalidade com base no remetente e no tipo
// de conteúdo.
//
// Principais Funcionalidades:
//
// 1. Distinção de Remetente: Aplica estilos e avatares diferentes para mensagens enviadas
//    pelo 'usuário' (`FiUser`) e pelo 'bot' (`FiCpu`).
//
// 2. Renderização de Conteúdo Dinâmico: É capaz de renderizar múltiplos tipos de conteúdo.
//    Se o conteúdo for do tipo 'text', exibe um parágrafo simples. Se for 'chart', renderiza
//    o `ChartComponent` para exibir um gráfico interativo.
//
// 3. Interatividade (Visualizador de Query): Para mensagens do bot que foram geradas a partir
//    de uma consulta ao banco, o componente exibe um botão "Ver Query". Ao ser clicado,
//    ele revela a query SQL exata que foi executada no backend, oferecendo transparência
//    e uma ótima ferramenta de depuração.
//
// 4. Gerenciamento de Estado Local: Utiliza o hook `useState` para controlar a visibilidade
//    do visualizador da query SQL, mantendo o estado de cada mensagem de forma independente.
//
// =================================================================================================
// =================================================================================================

import React, { useState } from 'react';
// Importa o componente filho responsável por renderizar os gráficos.
import ChartComponent from './ChartComponent';
// Importa os ícones da biblioteca `react-icons` para os avatares e botões.
import { FiUser, FiCpu, FiChevronDown, FiCode } from 'react-icons/fi'; 
// Importa a folha de estilos específica para este componente.
import './ChatMessage.css';

// Define o componente funcional, recebendo `sender` e `content` como propriedades (props).
const ChatMessage = ({ sender, content }) => {
  // Determina se a mensagem é do bot para aplicar lógica e estilos condicionais.
  const isBot = sender === 'bot';
  // Escolhe dinamicamente o ícone do avatar com base no remetente.
  const Avatar = isBot ? FiCpu : FiUser;

  // Cria uma variável de estado local para controlar a visibilidade da query SQL.
  // `isQueryVisible` armazena o estado (true/false), e `setIsQueryVisible` é a função para alterá-lo.
  // O valor inicial é `false`, ou seja, a query começa escondida.
  const [isQueryVisible, setIsQueryVisible] = useState(false);

  // Verifica se a mensagem atual deve ter o botão "Ver Query".
  // A condição é: a mensagem deve ser do bot E o objeto `content` deve possuir a chave `generated_sql`.
  const hasQuery = isBot && content.generated_sql;

  // Função chamada pelo evento `onClick` do botão para alternar a visibilidade da query.
  // Ela inverte o valor booleano atual de `isQueryVisible`.
  const toggleQueryVisibility = () => {
    setIsQueryVisible(!isQueryVisible);
  };

  // Constrói as classes CSS dinamicamente com base no remetente e tipo de conteúdo.
  let messageClasses = `message ${isBot ? 'bot-message' : 'user-message'}`;
  let wrapperClasses = `message-wrapper ${isBot ? 'bot-wrapper' : 'user-wrapper'}`;
  
  // Adiciona classes extras se a mensagem for um gráfico, para permitir estilização especial.
  if (content.type === 'chart') {
    messageClasses += ' has-chart';
    wrapperClasses += ' wrapper-has-chart';
  }

  // Função de renderização condicional para o conteúdo principal da mensagem.
  const renderContent = () => {
    // Se o tipo do conteúdo for 'chart', renderiza o componente de gráfico.
    if (content.type === 'chart') {
      return <ChartComponent chartData={content} />;
    }
    // Caso contrário, renderiza o texto dentro de um parágrafo.
    return <p>{content.content}</p>;
  };

  // Estrutura JSX que será renderizada pelo componente.
  return (
    <div className={wrapperClasses}>
      <div className="avatar">
        <Avatar />
      </div>
      <div className={messageClasses}>
        {/* Renderiza o conteúdo principal (texto ou gráfico) chamando a função. */}
        {renderContent()}

        {/* Renderiza o rodapé da mensagem apenas se for uma mensagem do bot. */}
        {isBot && (
          <div className="message-footer">
            {/* Exibe o tempo de resposta se essa informação estiver disponível. */}
            {content.response_time && (
              <div className="response-time-meta">
                <span>Gerado em {content.response_time}s</span>
              </div>
            )}

            {/* Renderiza o botão "Ver Query" apenas se `hasQuery` for verdadeiro. */}
            {hasQuery && (
              <button className="query-toggle-button" onClick={toggleQueryVisibility}>
                <FiCode size={14} /> 
                <span>Ver Query</span>
                {/* A seta gira para baixo quando a query está visível. */}
                <FiChevronDown size={14} className={`query-toggle-arrow ${isQueryVisible ? 'toggled' : ''}`} />
              </button>
            )}
          </div>
        )}
        
        {/* Renderiza a caixa de exibição da query SQL. */}
        {/* Esta seção só aparece se `hasQuery` E `isQueryVisible` forem ambos verdadeiros. */}
        {hasQuery && isQueryVisible && (
          <div className="query-display">
            {/* As tags `<pre>` e `<code>` são usadas para exibir código pré-formatado, preservando espaços e quebras de linha. */}
            <pre><code>{content.generated_sql}</code></pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;