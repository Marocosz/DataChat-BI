import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid, Legend } from 'recharts';
import { FiPackage, FiCheckCircle, FiTruck, FiDollarSign } from 'react-icons/fi';
import './Dashboard.css';

// Hook customizado final para busca de dados: seguro, com polling e cancelamento.
const useDataFetching = (endpoint) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const timeoutIdRef = useRef(null);

  useEffect(() => {
    let isMounted = true;
    const abortController = new AbortController();

    const fetchData = async () => {
      if (!isMounted) return;
      // Mostra "Carregando..." apenas na primeira busca
      if (!data) setLoading(true); 
      
      try {
        const response = await axios.get(`http://localhost:8000/api/dashboard/${endpoint}`, { signal: abortController.signal });
        if (isMounted) {
          setData(response.data);
          setError(null); // Limpa erros anteriores se a busca for bem-sucedida
        }
      } catch (err) {
        if (axios.isCancel(err)) {
          // Se a requisição foi cancelada, não fazemos nada.
          return;
        }
        if (isMounted) {
          setError("Falha ao carregar dados.");
        }
        console.error(`Failed to fetch ${endpoint}:`, err);
      } finally {
        if (isMounted) {
          setLoading(false);
          // Agenda a próxima busca de forma segura, apenas após a anterior terminar
          timeoutIdRef.current = setTimeout(fetchData, 15000);
        }
      }
    };

    fetchData(); // Busca os dados na montagem do componente

    // Função de limpeza: Roda quando o componente sai da tela
    return () => {
      isMounted = false;
      abortController.abort(); // Cancela qualquer requisição que ainda esteja em andamento
      clearTimeout(timeoutIdRef.current); // Cancela a próxima busca agendada
    };
  }, [endpoint]); // O array de dependências garante que o efeito só reinicie se o endpoint mudar

  return { data, loading, error };
};

// Componente para a grade de KPIs
const KpiGrid = () => {
  const { data: kpis, loading, error } = useDataFetching('kpis');
  
  const formatValue = (value, isCurrency = false) => {
    if (loading || value == null) return isCurrency ? 'R$ -' : '-';
    if (isCurrency) return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
    return new Intl.NumberFormat('pt-BR').format(value);
  };

  if (error) return <div className="kpi-grid-error">Não foi possível carregar os KPIs.</div>;

  return (
    <section className="kpi-grid">
      <div className="kpi-card"><div className="kpi-icon"><FiPackage /></div><div className="kpi-text"><h3>Total de Operações</h3><p>{formatValue(kpis?.total_operacoes)}</p></div></div>
      <div className="kpi-card"><div className="kpi-icon"><FiCheckCircle /></div><div className="kpi-text"><h3>Operações Entregues</h3><p>{formatValue(kpis?.operacoes_entregues)}</p></div></div>
      <div className="kpi-card"><div className="kpi-icon"><FiTruck /></div><div className="kpi-text"><h3>Em Trânsito</h3><p>{formatValue(kpis?.operacoes_em_transito)}</p></div></div>
      <div className="kpi-card"><div className="kpi-icon"><FiDollarSign /></div><div className="kpi-text"><h3>Valor Total das Mercadorias</h3><p>{formatValue(kpis?.valor_total_mercadorias, true)}</p></div></div>
    </section>
  );
};

// Componente para um card de gráfico individual
const ChartWrapper = ({ title, endpoint, children }) => {
  const { data, loading, error } = useDataFetching(endpoint);

  if (loading) return <div className="chart-section loading"><h2>{title}</h2><div className="dashboard-state">Carregando...</div></div>;
  if (error) return <div className="chart-section error"><h2>{title}</h2><div className="dashboard-state">{error}</div></div>;
  if (!Array.isArray(data) || data.length === 0) return <div className="chart-section empty"><h2>{title}</h2><div className="dashboard-state">Nenhum dado encontrado.</div></div>;
  
  return <section className="chart-section"><h2>{title}</h2>{children(data)}</section>;
};

// Componente principal do Dashboard
function Dashboard() {
  const COLORS = ['#5e72e4', '#2dce89', '#ff8d4e', '#f5365c', '#11cdef'];
  const abbreviateStatus = (statusName) => ({ 'SOLICITADO': 'Solicitado', 'AGUARDANDO_COLETA': 'Aguard. Coleta', 'EM_TRANSITO': 'Em Trânsito', 'ARMAZENADO': 'Armazenado', 'EM_ROTA_DE_ENTREGA': 'Em Entrega', 'ENTREGUE': 'Entregue', 'CANCELADO': 'Cancelado' }[statusName] || statusName);
  const formatYAxisTick = (tick) => tick >= 1000 ? `${tick / 1000}k` : tick;
  const formatCurrency = (value) => value != null ? new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value) : "R$ 0,00";

  return (
    <div className="dashboard">
      <header className="dashboard-header"><h1>Dashboard de Logística</h1><p>Visão geral das operações.</p></header>
      <KpiGrid />
      <div className="charts-grid">
        <ChartWrapper title="Operações por Status" endpoint="operacoes_por_status">
            {(data) => (<ResponsiveContainer width="100%" height={400}><BarChart data={data.map(item => ({ ...item, name: abbreviateStatus(item.name) }))}><XAxis dataKey="name" stroke="var(--text-secondary)" interval={0} tick={{ fontSize: 12 }} /><YAxis stroke="var(--text-secondary)" tickFormatter={formatYAxisTick} /><Tooltip cursor={{ fill: 'var(--primary-light)' }} /><Bar dataKey="value" radius={[4, 4, 0, 0]}>{data.map((entry, index) => (<Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />))}</Bar></BarChart></ResponsiveContainer>)}
        </ChartWrapper>
        <ChartWrapper title="Top 10 Estados por Valor de Frete" endpoint="valor_frete_por_uf">
            {(data) => (<ResponsiveContainer width="100%" height={400}><BarChart data={data}><XAxis dataKey="name" stroke="var(--text-secondary)" interval={0} tick={{ fontSize: 12 }} /><YAxis stroke="var(--text-secondary)" tickFormatter={(value) => `R$${formatYAxisTick(value)}`} /><Tooltip formatter={(value) => formatCurrency(value)} cursor={{ fill: 'var(--primary-light)' }} /><Bar dataKey="value" radius={[4, 4, 0, 0]} fill="#2dce89" /></BarChart></ResponsiveContainer>)}
        </ChartWrapper>
        <ChartWrapper title="Operações Criadas (Últimos 30 dias)" endpoint="operacoes_por_dia">
            {(data) => (<ResponsiveContainer width="100%" height={400}><LineChart data={data}><CartesianGrid strokeDasharray="3 3" stroke={"var(--border-color)"} /><XAxis dataKey="name" stroke="var(--text-secondary)" /><YAxis stroke="var(--text-secondary)" /><Tooltip /><Legend /><Line type="monotone" dataKey="value" name="Nº de Operações" stroke="#ff8d4e" /></LineChart></ResponsiveContainer>)}
        </ChartWrapper>
        <ChartWrapper title="Top 5 Clientes por Valor de Mercadoria" endpoint="top_clientes_por_valor">
            {(data) => (<ResponsiveContainer width="100%" height={400}><PieChart><Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={150} label={({ name, percent }) => `${name.split(' ')[0]} (${(percent * 100).toFixed(0)}%)`}>{data.map((entry, index) => (<Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />))}</Pie><Tooltip formatter={(value) => formatCurrency(value)} /><Legend /></PieChart></ResponsiveContainer>)}
        </ChartWrapper>
      </div>
    </div>
  );
}

export default Dashboard;