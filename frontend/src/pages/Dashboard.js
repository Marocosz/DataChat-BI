import React, { useState, useEffect, useRef } from 'react'; // Importar useRef
import axios from 'axios';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid, Legend } from 'recharts';
import { FiPackage, FiCheckCircle, FiTruck, FiDollarSign } from 'react-icons/fi';
import './Dashboard.css';

// --- COMPONENTES E FUNÇÕES AUXILIARES (sem alteração) ---
const KpiCard = ({ title, value, unit, icon }) => (
  <div className="kpi-card">
    <div className="kpi-icon">{icon}</div>
    <div className="kpi-text">
      <h3>{title}</h3>
      <p>{value !== null && value !== undefined ? value : '-'} <span>{unit}</span></p>
    </div>
  </div>
);

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip">
        <p className="label">{`${label}`}</p>
        <p className="intro">{`Total: ${new Intl.NumberFormat('pt-BR').format(payload[0].value)} operações`}</p>
      </div>
    );
  }
  return null;
};
const formatCurrency = (value) => {
  if (value === null || value === undefined) return "R$ 0,00";
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
};
const formatYAxisTick = (tick) => {
  if (tick >= 1000000) return `${tick / 1000000}M`;
  if (tick >= 1000) return `${tick / 1000}k`;
  return tick;
};
const abbreviateStatus = (statusName) => {
  const mapping = { 'SOLICITADO': 'Solicitado', 'AGUARDANDO_COLETA': 'Aguard. Coleta', 'EM_TRANSITO': 'Em Trânsito', 'ARMAZENADO': 'Armazenado', 'EM_ROTA_DE_ENTREGA': 'Em Entrega', 'ENTREGUE': 'Entregue', 'CANCELADO': 'Cancelado' };
  return mapping[statusName] || statusName;
};

// --- COMPONENTE PRINCIPAL DO DASHBOARD ---
function Dashboard() {
  const [kpis, setKpis] = useState(null);
  const [statusData, setStatusData] = useState([]);
  const [freteUfData, setFreteUfData] = useState([]);
  const [tendenciaData, setTendenciaData] = useState([]);
  const [topClientesData, setTopClientesData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Usamos um ref para guardar o ID do timeout e poder limpá-lo
  const timeoutIdRef = useRef(null);

  const COLORS = ['#5e72e4', '#2dce89', '#ff8d4e', '#f5365c', '#11cdef'];

  // --- INÍCIO DA ATUALIZAÇÃO: LÓGICA DE BUSCA DE DADOS CORRIGIDA ---
  useEffect(() => {
    // Definimos a função de busca de dados aqui dentro
    const fetchData = async () => {
      // Não resetamos o erro a cada 5s para não piscar na tela
      // Apenas na carga inicial
      if (loading) setError(null);
      
      try {
        const [kpiRes, statusRes, freteRes, tendenciaRes, topClientesRes] = await Promise.all([
          axios.get('http://localhost:8000/api/dashboard/kpis'),
          axios.get('http://localhost:8000/api/dashboard/operacoes_por_status'),
          axios.get('http://localhost:8000/api/dashboard/valor_frete_por_uf'),
          axios.get('http://localhost:8000/api/dashboard/operacoes_por_dia'),
          axios.get('http://localhost:8000/api/dashboard/top_clientes_por_valor')
        ]);

        const abbreviatedData = statusRes.data.map(item => ({ ...item, name: abbreviateStatus(item.name) }));

        setKpis(kpiRes.data);
        setStatusData(abbreviatedData);
        setFreteUfData(freteRes.data);
        setTendenciaData(tendenciaRes.data);
        setTopClientesData(topClientesRes.data);

        // Se a busca deu certo, agendamos a PRÓXIMA para daqui a 5 segundos
        timeoutIdRef.current = setTimeout(fetchData, 5000);

      } catch (err) {
        setError("Falha ao buscar dados do servidor. Verifique se o backend está rodando.");
        console.error("Failed to fetch dashboard data:", err);
        // Se deu erro, tentamos de novo em 5 segundos
        timeoutIdRef.current = setTimeout(fetchData, 5000);
      } finally {
        // Só paramos de carregar na primeira vez
        if (loading) setLoading(false);
      }
    };

    // Chamamos a função pela primeira vez
    fetchData();

    // Esta é a função de limpeza. Ela será chamada quando o componente "morrer".
    // Isso garante que, se o usuário sair da página do dashboard, a busca de dados pare.
    return () => {
      clearTimeout(timeoutIdRef.current);
    };
  }, []); // O array vazio [] garante que este useEffect SÓ RODA UMA VEZ na montagem.
  // --- FIM DA ATUALIZAÇÃO ---


  if (loading) {
    return <div className="dashboard-state">Carregando dados...</div>;
  }
  if (error && !kpis) { // Só mostra o erro em tela cheia se não tiver NENHUM dado
    return <div className="dashboard-state error">{error}</div>;
  }

  // --- RENDERIZAÇÃO DO JSX (sem alterações) ---
  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Dashboard de Logística</h1>
        <p>Visão geral das operações em tempo real.</p>
        {error && <div className="dashboard-error-banner">{error}</div>}
      </header>
      
      <section className="kpi-grid">
        <KpiCard title="Total de Operações" value={kpis?.total_operacoes ? new Intl.NumberFormat('pt-BR').format(kpis.total_operacoes) : '-'} icon={<FiPackage />} />
        <KpiCard title="Operações Entregues" value={kpis?.operacoes_entregues ? new Intl.NumberFormat('pt-BR').format(kpis.operacoes_entregues) : '-'} icon={<FiCheckCircle />} />
        <KpiCard title="Em Trânsito" value={kpis?.operacoes_em_transito ? new Intl.NumberFormat('pt-BR').format(kpis.operacoes_em_transito) : '-'} icon={<FiTruck />} />
        <KpiCard title="Valor Total das Mercadorias" value={formatCurrency(kpis?.valor_total_mercadorias)} icon={<FiDollarSign />} />
      </section>

      <div className="charts-grid">
        <section className="chart-section">
          <h2>Operações por Status</h2>
          {statusData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={statusData} margin={{ top: 5, right: 30, left: 20, bottom: 20 }}>
                <XAxis dataKey="name" stroke="var(--text-secondary)" interval={0} tick={{ fontSize: 12 }} />
                <YAxis stroke="var(--text-secondary)" tickFormatter={formatYAxisTick} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--primary-light)' }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {statusData.map((entry, index) => (<Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (<div className="dashboard-state">Nenhum dado de status.</div>)}
        </section>
        
        <section className="chart-section">
          <h2>Top 10 Estados por Valor de Frete</h2>
          {freteUfData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={freteUfData} margin={{ top: 5, right: 30, left: 20, bottom: 20 }}>
                <XAxis dataKey="name" stroke="var(--text-secondary)" interval={0} tick={{ fontSize: 12 }} />
                <YAxis stroke="var(--text-secondary)" tickFormatter={(value) => `R$${formatYAxisTick(value)}`} />
                <Tooltip formatter={(value) => formatCurrency(value)} cursor={{ fill: 'var(--primary-light)' }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]} fill="#2dce89" />
              </BarChart>
            </ResponsiveContainer>
          ) : (<div className="dashboard-state">Nenhum dado de frete.</div>)}
        </section>
        
        <section className="chart-section">
          <h2>Operações Criadas (Últimos 30 dias)</h2>
          {tendenciaData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={tendenciaData} margin={{ top: 5, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={"var(--border-color)"} />
                <XAxis dataKey="name" stroke="var(--text-secondary)" />
                <YAxis stroke="var(--text-secondary)" />
                <Tooltip contentStyle={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-color)' }} />
                <Legend />
                <Line type="monotone" dataKey="value" name="Nº de Operações" stroke="#ff8d4e" strokeWidth={2} activeDot={{ r: 8 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (<div className="dashboard-state">Nenhuma tendência de dados.</div>)}
        </section>
        
        <section className="chart-section">
          <h2>Top 5 Clientes por Valor de Mercadoria</h2>
          {topClientesData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <PieChart>
                <Pie data={topClientesData} cx="50%" cy="50%" labelLine={false} outerRadius={150} fill="#8884d8" dataKey="value" nameKey="name" label={({ name, percent }) => `${name.split(' ')[0]} (${(percent * 100).toFixed(0)}%)`}>
                  {topClientesData.map((entry, index) => (<Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />))}
                </Pie>
                <Tooltip formatter={(value) => formatCurrency(value)} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (<div className="dashboard-state">Nenhum dado de cliente.</div>)}
        </section>
      </div>
    </div>
  );
}

export default Dashboard;