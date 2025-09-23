import React from 'react';
import { 
  BarChart, Bar, 
  LineChart, Line, 
  PieChart, Pie,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid, Legend 
} from 'recharts';

// --- FUNÇÕES E COMPONENTES AUXILIARES ---
const formatCurrency = (value) => {
  if (value === null || value === undefined) return "R$ 0,00";
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
};

// Tooltip para gráficos de Barra e Linha
const CustomTooltip = ({ active, payload, label, y_axis_label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="label">{`${label}`}</p>
          <p className="intro">{`${y_axis_label || 'Valor'}: ${new Intl.NumberFormat('pt-BR').format(payload[0].value)}`}</p>
        </div>
      );
    }
    return null;
};

// Tooltip específico para o Gráfico de Pizza
const CustomPieTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const name = data.name; // O nameKey já foi resolvido para 'name'
      const value = data.value; // O dataKey já foi resolvido para 'value'

      return (
        <div className="custom-tooltip">
          <p className="label">{name}</p>
          {/* Mostra o valor formatado como número, não como moeda */}
          <p className="intro">{`Valor: ${new Intl.NumberFormat('pt-BR').format(value)}`}</p>
          <p className="intro">{`Percentual: ${(payload[0].percent * 100).toFixed(1)}%`}</p>
        </div>
      );
    }
    return null;
};

// --- COMPONENTE PRINCIPAL ---
function ChartComponent({ chartData }) {
  const { title, data, x_axis, y_axis, y_axis_label, chart_type } = chartData;
  const COLORS = ['#5e72e4', '#2dce89', '#ff8d4e', '#f5365c', '#11cdef', '#fb6340', '#ffd600'];

  const renderChart = () => {
    // --- LÓGICA PRINCIPAL DA CORREÇÃO ---
    // Pega os nomes das chaves dinamicamente do JSON enviado pela IA.
    const yAxisKey = y_axis ? y_axis[0] : 'value';
    const xAxisKey = x_axis || 'name';
    const yAxisLabel = y_axis_label || yAxisKey; // Usa o nome da chave como fallback
    
    // O Recharts espera que as chaves sejam 'name' e 'value' no tooltip de pizza.
    // Então, mapeamos os dados para esse formato padronizado.
    const processedData = data.map(item => ({
        ...item,
        name: item[xAxisKey],
        value: item[yAxisKey]
    }));
    // ------------------------------------

    switch (chart_type) {
      case 'line':
        return (
          <LineChart data={processedData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={"var(--border-color)"} />
            <XAxis dataKey="name" stroke="var(--text-secondary)" interval={0} tick={{ fontSize: 11 }} />
            <YAxis stroke="var(--text-secondary)" />
            <Tooltip content={<CustomTooltip y_axis_label={yAxisLabel} />} />
            <Legend verticalAlign="top" wrapperStyle={{ paddingBottom: '20px' }} />
            <Line type="monotone" dataKey="value" name={yAxisLabel} stroke="#ff8d4e" strokeWidth={2} activeDot={{ r: 8 }} />
          </LineChart>
        );
      
      case 'pie':
        return (
          <PieChart>
            <Pie
              data={processedData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={false}
              outerRadius="80%"
              fill="#8884d8"
              dataKey="value" // Agora sempre será 'value'
              nameKey="name"   // Agora sempre será 'name'
            >
              {processedData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomPieTooltip />} />
            <Legend /> 
          </PieChart>
        );

      case 'bar':
      default:
        return (
            <BarChart data={processedData} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={"var(--border-color)"} />
                <XAxis dataKey="name" stroke="var(--text-secondary)" interval={0} tick={{ fontSize: 11 }} />
                <YAxis stroke="var(--text-secondary)" />
                <Tooltip content={<CustomTooltip y_axis_label={yAxisLabel} />} cursor={{fill: 'var(--primary-light)'}} />
                <Legend verticalAlign="top" wrapperStyle={{ paddingBottom: '20px' }} />
                <Bar dataKey="value" name={yAxisLabel} radius={[4, 4, 0, 0]}>
                    {processedData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                </Bar>
            </BarChart>
        );
    }
  };

  return (
    <div className="chart-container">
      <h4>{title}</h4>
      <ResponsiveContainer width="100%" height={300}>
        {renderChart()}
      </ResponsiveContainer>
    </div>
  );
}

export default ChartComponent;