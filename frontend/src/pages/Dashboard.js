// =================================================================================================
// =================================================================================================
//
//                         COMPONENTE DA PÁGINA DO DASHBOARD
//
// Visão Geral do Arquivo:
//
// Este arquivo define a página de Dashboard completa, que exibe visualizações de dados e
// indicadores chave de performance (KPIs) sobre as operações logísticas. A arquitetura
// do arquivo é dividida em quatro partes principais para máxima reutilização e clareza:
//
// 1. useDataFetching (Hook Customizado):
//    - Um hook React reutilizável que encapsula toda a lógica de busca de dados da API.
//    - Gerencia os estados de carregamento (loading), erro e os dados recebidos.
//    - Implementa um mecanismo de "polling" que atualiza os dados automaticamente a cada
//      15 segundos, criando um dashboard "ao vivo".
//
// 2. KpiGrid (Componente de Apresentação):
//    - Um componente dedicado a buscar e exibir a grade de KPIs no topo da página.
//
// 3. ChartWrapper (Componente Container/Wrapper):
//    - Um invólucro genérico para cada gráfico. Ele utiliza o hook `useDataFetching` para
//      buscar os dados do gráfico e lida com a exibição dos estados de carregamento,
//      erro ou dados vazios. Isso mantém o componente principal do Dashboard limpo.
//
// 4. Dashboard (Componente Principal da Página):
//    - Monta o layout completo da página, incluindo o cabeçalho, a grade de KPIs e
//      múltiplas instâncias do `ChartWrapper` para renderizar cada gráfico específico.
//
// =================================================================================================
// =================================================================================================

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
// Importa todos os componentes necessários da biblioteca de gráficos `recharts`.
import { BarChart, Bar, LineChart, Line, PieChart, Pie, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid, Legend } from 'recharts';
// Importa ícones para os cards de KPI.
import { FiPackage, FiCheckCircle, FiTruck, FiDollarSign } from 'react-icons/fi';
// Importa a folha de estilos específica para este componente.
import './Dashboard.css';

// --- Hook Customizado para Busca de Dados com Polling ---

// Este hook encapsula a lógica de buscar dados de um endpoint da API de forma reutilizável.
const useDataFetching = (endpoint) => {
  // Estados para armazenar os dados, o status de carregamento e possíveis erros.
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  // `useRef` para guardar o ID do timer do polling, permitindo limpá-lo depois.
  const timeoutIdRef = useRef(null);

  // `useEffect` gerencia o ciclo de vida da busca de dados.
  useEffect(() => {
    let isMounted = true; // Flag para evitar atualizações de estado se o componente for desmontado.
    const abortController = new AbortController(); // Permite cancelar a requisição se o componente for desmontado.

    const fetchData = async () => {
      if (!isMounted) return;
      // Mostra o loading apenas na primeira busca, para evitar piscar a tela nas atualizações.
      if (!data) setLoading(true); 
      
      try {
        const response = await axios.get(`http://localhost:8000/api/dashboard/${endpoint}`, { signal: abortController.signal });
        if (isMounted) {
          setData(response.data); // Armazena os dados no estado.
          setError(null); // Limpa qualquer erro anterior.
        }
      } catch (err) {
        if (axios.isCancel(err)) return; // Ignora erros de cancelamento.
        if (isMounted) setError("Falha ao carregar.");
        console.error(`Failed to fetch ${endpoint}:`, err);
      } finally {
        if (isMounted) {
          setLoading(false); // Finaliza o estado de carregamento.
          // Polling: Agenda a próxima busca de dados para daqui a 15 segundos.
          timeoutIdRef.current = setTimeout(fetchData, 15000);
        }
      }
    };

    fetchData(); // Executa a busca de dados na montagem do componente.

    // Função de limpeza: executada quando o componente é desmontado.
    return () => {
      isMounted = false;
      abortController.abort(); // Cancela qualquer requisição em andamento.
      clearTimeout(timeoutIdRef.current); // Cancela o próximo polling agendado para evitar memory leaks.
    };
  }, [endpoint]); // Roda o efeito novamente se o endpoint mudar.

  // O hook retorna seu estado para o componente que o utiliza.
  return { data, loading, error };
};

// --- Componente para a Grade de KPIs ---

const KpiGrid = () => {
  // Utiliza o hook customizado para buscar os dados do endpoint 'kpis'.
  const { data: kpis, loading, error } = useDataFetching('kpis');
  
  // Função auxiliar para formatar os valores dos KPIs, lidando com o estado de carregamento.
  const formatValue = (value, isCurrency = false) => {
    if (loading || value == null) return isCurrency ? 'R$ -' : '-';
    if (isCurrency) return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
    return new Intl.NumberFormat('pt-BR').format(value);
  };

  if (error) return <div className="kpi-grid-error">Não foi possível carregar os KPIs.</div>;

  // Renderiza a grade de cards de KPI.
  return (
    <section className="kpi-grid">
      <div className="kpi-card"><div className="kpi-icon"><FiPackage /></div><div className="kpi-text"><h3>Total de Operações</h3><p>{formatValue(kpis?.total_operacoes)}</p></div></div>
      <div className="kpi-card"><div className="kpi-icon"><FiCheckCircle /></div><div className="kpi-text"><h3>Operações Entregues</h3><p>{formatValue(kpis?.operacoes_entregues)}</p></div></div>
      <div className="kpi-card"><div className="kpi-icon"><FiTruck /></div><div className="kpi-text"><h3>Em Trânsito</h3><p>{formatValue(kpis?.operacoes_em_transito)}</p></div></div>
      <div className="kpi-card"><div className="kpi-icon"><FiDollarSign /></div><div className="kpi-text"><h3>Valor Total das Mercadorias</h3><p>{formatValue(kpis?.valor_total_mercadorias, true)}</p></div></div>
    </section>
  );
};

// --- Componente Wrapper para Gráficos ---

// Este componente encapsula a lógica de busca e estado para um gráfico individual.
const ChartWrapper = ({ title, endpoint, children }) => {
  const { data, loading, error } = useDataFetching(endpoint);

  // Renderização condicional com base no estado do hook de busca.
  if (loading) return <div className="chart-section loading"><h2>{title}</h2><div className="dashboard-state">Carregando...</div></div>;
  if (error) return <div className="chart-section error"><h2>{title}</h2><div className="dashboard-state">{error}</div></div>;
  if (!Array.isArray(data) || data.length === 0) return <div className="chart-section empty"><h2>{title}</h2><div className="dashboard-state">Nenhum dado encontrado.</div></div>;
  
  // Se os dados foram carregados com sucesso, renderiza o gráfico.
  // Utiliza o padrão "render prop", passando os dados para a função filha.
  return <section className="chart-section"><h2>{title}</h2>{children(data)}</section>;
};

// --- Componente Principal do Dashboard ---

function Dashboard() {
  // Paleta de cores e funções auxiliares de formatação para os gráficos.
  const COLORS = ['#5e72e4', '#2dce89', '#ff8d4e', '#f5365c', '#11cdef'];
  const abbreviateStatus = (statusName) => ({ 'SOLICITADO': 'Solicitado', 'AGUARDANDO_COLETA': 'Aguard. Coleta', 'EM_TRANSITO': 'Em Trânsito', 'ARMAZENADO': 'Armazenado', 'EM_ROTA_DE_ENTREGA': 'Em Entrega', 'ENTREGUE': 'Entregue', 'CANCELADO': 'Cancelado' }[statusName] || statusName);
  const formatYAxisTick = (tick) => tick >= 1000 ? `${tick / 1000}k` : tick;
  const formatCurrency = (value) => value != null ? new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value) : "R$ 0,00";
  
  // Estilo padrão para os tooltips, alinhado com o tema escuro.
  const tooltipStyle = {
    backgroundColor: '#1a1d24',
    border: '1px solid var(--border-color)',
    borderRadius: '8px',
    color: 'var(--text-primary)'
  };

  // Renderiza a estrutura completa da página.
  return (
    <div className="dashboard">
      <header className="dashboard-header"><h1>Dashboard de Logística</h1><p>Visão geral das operações.</p></header>
      <KpiGrid />
      <div className="charts-grid">
        {/* Gráfico 1: Operações por Status */}
        <ChartWrapper title="Operações por Status" endpoint="operacoes_por_status">
          {(data) => (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={data.map(item => ({ ...item, name: abbreviateStatus(item.name) }))}>
                <XAxis dataKey="name" stroke="var(--text-secondary)" interval={0} tick={{ fontSize: 12 }} />
                <YAxis stroke="var(--text-secondary)" tickFormatter={formatYAxisTick} />
                <Tooltip cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }} contentStyle={tooltipStyle} itemStyle={{ color: 'white' }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {data.map((entry, index) => (<Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartWrapper>

        {/* Gráfico 2: Top 10 Estados por Frete */}
        <ChartWrapper title="Top 10 Estados por Valor de Frete" endpoint="valor_frete_por_uf">
          {(data) => (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={data}>
                <XAxis dataKey="name" stroke="var(--text-secondary)" interval={0} tick={{ fontSize: 12 }} />
                <YAxis stroke="var(--text-secondary)" tickFormatter={(value) => `R$${formatYAxisTick(value)}`} />
                <Tooltip formatter={(value) => formatCurrency(value)} cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }} contentStyle={tooltipStyle} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]} fill="#2dce89" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartWrapper>

        {/* Gráfico 3: Operações criadas nos últimos 30 dias */}
        <ChartWrapper title="Operações Criadas (Últimos 30 dias)" endpoint="operacoes_por_dia">
          {(data) => (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke={"var(--border-color)"} />
                <XAxis dataKey="name" stroke="var(--text-secondary)" />
                <YAxis stroke="var(--text-secondary)" />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend />
                <Line type="monotone" dataKey="value" name="Nº de Operações" stroke="#ff8d4e" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartWrapper>
        
        {/* Gráfico 4: Top 5 Clientes por Valor */}
        <ChartWrapper title="Top 5 Clientes por Valor de Mercadoria" endpoint="top_clientes_por_valor">
          {(data) => (
            <ResponsiveContainer width="100%" height={400}>
              <PieChart>
                <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={150} label={({ name, percent }) => `${name.split(' ')[0]} (${(percent * 100).toFixed(0)}%)`}>
                  {data.map((entry, index) => (<Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />))}
                </Pie>
                <Tooltip formatter={(value) => formatCurrency(value)} contentStyle={tooltipStyle} itemStyle={{ color: 'white' }} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartWrapper>
      </div>
    </div>
  );
}

export default Dashboard;