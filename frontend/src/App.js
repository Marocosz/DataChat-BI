// =================================================================================================
// =================================================================================================
//
//                       COMPONENTE RAIZ E ROTEADOR DA APLICAÇÃO
//
// Visão Geral do Componente:
//
// Este arquivo define o componente `App`, que serve como o ponto de entrada e o componente
// de mais alto nível para toda a aplicação React. Sua principal responsabilidade é definir
// a estrutura de layout geral e gerenciar o sistema de roteamento de páginas.
//
// Principais Funcionalidades:
//
// 1. Configuração do Roteador: Utiliza o `react-router-dom` para habilitar a navegação
//    entre diferentes "páginas" (componentes) da aplicação sem a necessidade de recarregar
//    a página inteira, criando uma experiência de Single-Page Application (SPA).
//
// 2. Layout Persistente: Renderiza componentes comuns que devem aparecer em todas as
//    páginas, como a barra de navegação (`Navbar`), garantindo uma interface consistente.
//
// 3. Mapeamento de Rotas: Define quais componentes de página (`Dashboard`, `Chat`) devem
//    ser renderizados com base na URL atual do navegador. Por exemplo, a URL "/" renderiza
//    o Dashboard, enquanto "/chat" renderiza a página de Chat.
//
// =================================================================================================
// =================================================================================================

import React from 'react';
// Importa os componentes necessários do `react-router-dom` para gerenciar o roteamento.
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
// Importa os componentes de layout e de página.
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
// Importa a folha de estilos principal da aplicação.
import './App.css';

// Define o componente raiz da aplicação.
function App() {
  return (
    // O componente `Router` (apelido de `BrowserRouter`) envolve toda a aplicação,
    // ativando o sistema de roteamento baseado na URL do navegador.
    <Router>
      <div className="App">
        {/* O componente `Navbar` é renderizado aqui, fora do sistema de `Routes`,
             o que o torna persistente e visível em todas as páginas da aplicação. */}
        <Navbar />
        {/* O elemento `main` serve como o container principal para o conteúdo
             que mudará de acordo com a rota. */}
        <main className="content">
          {/* O componente `Routes` funciona como um "switch", que renderiza o primeiro
               `Route` que corresponder à URL atual. */}
          <Routes>
            {/* Define a rota para a página inicial ("/").
                 Quando a URL for a raiz do site, o componente `Dashboard` será renderizado. */}
            <Route path="/" element={<Dashboard />} />
            {/* Define a rota para a página de chat ("/chat").
                 Quando a URL for "/chat", o componente `Chat` será renderizado. */}
            <Route path="/chat" element={<Chat />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;