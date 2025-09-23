import React from 'react';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid, Legend,
  Label
} from 'recharts';

// --- FUNÇÕES E COMPONENTES AUXILIARES ---

const formatCurrency = (value) => {/* ...código sem alteração... */};
const CustomPieTooltip = ({ active, payload }) => {/* ...código sem alteração... */};

// Tooltip para Barra/Linha agora mostra o nome completo do eixo X
const CustomTooltip = ({ active, payload, label, y_axis_label }) => {
    if (active && payload && payload.length) {
      // Usamos payload[0].payload.name para garantir que pegamos o nome completo original
      const fullLabel = payload[0].payload.name;
      return (
        <div className="custom-tooltip">
          <p className="label">{`${fullLabel}`}</p>
          <p className="intro">{`${y_axis_label || 'Valor'}: ${new Intl.NumberFormat('pt-BR').format(payload[0].value)}`}</p>
        </div>
      );
    }
    return null;
};

// --- NOVA FUNÇÃO PARA ABREVIAR NOMES ---
const shortenLabel = (name) => {
    if (typeof name !== 'string') return '';
    const words = name.split(' ');
    if (words.length > 1) {
        // Pega a primeira palavra e a primeira letra da segunda, ex: "Abreu Ltda." -> "Abreu L."
        return `${words[0]} ${words[1].charAt(0)}.`;
    }
    return name;
};


// --- COMPONENTE PRINCIPAL ---

function ChartComponent({ chartData }) {
  const { title, data, x_axis, y_axis, y_axis_label, chart_type } = chartData;
  const COLORS = ['#5e72e4', '#2dce89', '#ff8d4e', '#f5365c', '#11cdef', '#fb6340', '#ffd600'];

  const renderChart = () => {
    const yAxisKey = y_axis ? y_axis[0] : 'value';
    const xAxisKey = x_axis || 'name';
    const yAxisLabel = y_axis_label || yAxisKey;
    
    // Processamento de dados agora também cria um nome abreviado
    const processedData = data.map(item => ({
        ...item,
        name: item[xAxisKey],       // Nome completo para o tooltip
        shortName: shortenLabel(item[xAxisKey]), // Nome curto para o eixo X
        value: item[yAxisKey]
    }));

    switch (chart_type) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={processedData} margin={{ top: 5, right: 30, left: 30, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={"var(--border-color)"} />
              <XAxis dataKey="shortName" stroke="var(--text-secondary)" tick={{ fontSize: 11 }} />
              <YAxis stroke="var(--text-secondary)">
                <Label value={yAxisLabel} angle={-90} position="insideLeft" style={{ textAnchor: 'middle', fill: 'var(--text-secondary)' }} />
              </YAxis>
              <Tooltip content={<CustomTooltip y_axis_label={yAxisLabel} />} />
              <Line type="monotone" dataKey="value" name={yAxisLabel} stroke="#ff8d4e" strokeWidth={2} activeDot={{ r: 8 }} />
            </LineChart>
          </ResponsiveContainer>
        );
      
      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={processedData}
                dataKey="value"
                nameKey="name" // O tooltip da pizza usa o nome completo
                cx="50%"
                cy="50%"
                outerRadius="80%"
                labelLine={false}
                label={false}
              >
                {processedData.map((entry, index) => (<Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />))}
              </Pie>
              <Tooltip content={<CustomPieTooltip />} />
              {/* Adicionado espaçamento para não sobrepor o gráfico */}
              <Legend wrapperStyle={{ paddingTop: '20px' }} /> 
            </PieChart>
          </ResponsiveContainer>
        );

      case 'bar':
      default:
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={processedData} margin={{ top: 5, right: 20, left: 30, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={"var(--border-color)"} />
                {/* Eixo X agora usa o nome abreviado 'shortName' */}
                <XAxis dataKey="shortName" stroke="var(--text-secondary)" tick={{ fontSize: 11 }} />
                <YAxis stroke="var(--text-secondary)">
                    <Label value={yAxisLabel} angle={-90} position="insideLeft" style={{ textAnchor: 'middle', fill: 'var(--text-secondary)' }} />
                </YAxis>
                {/* O Tooltip continua usando o nome completo via 'CustomTooltip' */}
                <Tooltip content={<CustomTooltip y_axis_label={yAxisLabel} />} cursor={{fill: 'var(--primary-light)'}} />
                <Bar dataKey="value" name={yAxisLabel} radius={[4, 4, 0, 0]}>
                    {processedData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                </Bar>
            </BarChart>
          </ResponsiveContainer>
        );
    }
  };

  return (
    <div className="chart-container">
      <h4>{title}</h4>
      {renderChart()}
    </div>
  );
}

export default ChartComponent;