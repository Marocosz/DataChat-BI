// src/components/ChartComponent.js (Versão Final e Completa)
import React from 'react';
import { 
  BarChart, Bar, 
  LineChart, Line, 
  PieChart, Pie,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid, Legend 
} from 'recharts';

// Funções auxiliares
const formatCurrency = (value) => {
  if (value === null || value === undefined) return "R$ 0,00";
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
};

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

function ChartComponent({ chartData }) {
  const { title, data, x_axis, y_axis, y_axis_label, chart_type } = chartData;
  const COLORS = ['#5e72e4', '#2dce89', '#ff8d4e', '#f5365c', '#11cdef', '#fb6340', '#ffd600'];

  const renderChart = () => {
    const yAxisKey = y_axis ? y_axis[0] : 'value';
    const xAxisKey = x_axis || 'name';
    const yAxisLabel = y_axis_label || 'Valor';

    switch (chart_type) {
      case 'line':
        return (
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={"var(--border-color)"} />
            <XAxis dataKey={xAxisKey} stroke="var(--text-secondary)" interval={0} tick={{ fontSize: 11 }} />
            <YAxis stroke="var(--text-secondary)" />
            <Tooltip content={<CustomTooltip y_axis_label={yAxisLabel} />} />
            <Legend verticalAlign="top" wrapperStyle={{ paddingBottom: '20px' }} />
            <Line type="monotone" dataKey={yAxisKey} name={yAxisLabel} stroke="#ff8d4e" strokeWidth={2} activeDot={{ r: 8 }} />
          </LineChart>
        );
      
      case 'pie':
        return (
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              outerRadius={120}
              fill="#8884d8"
              dataKey={yAxisKey}
              nameKey={xAxisKey}
              label={({ name, percent }) => `${name.split(' ')[0]} (${(percent * 100).toFixed(0)}%)`}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => formatCurrency(value)} />
            <Legend />
          </PieChart>
        );

      case 'bar':
      default:
        return (
            <BarChart data={data} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={"var(--border-color)"} />
                <XAxis dataKey={xAxisKey} stroke="var(--text-secondary)" interval={0} tick={{ fontSize: 11 }} />
                <YAxis stroke="var(--text-secondary)" />
                <Tooltip content={<CustomTooltip y_axis_label={yAxisLabel} />} cursor={{fill: 'var(--primary-light)'}} />
                <Legend verticalAlign="top" wrapperStyle={{ paddingBottom: '20px' }} />
                <Bar dataKey={yAxisKey} name={yAxisLabel} radius={[4, 4, 0, 0]}>
                    {data.map((entry, index) => (
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