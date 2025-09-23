import React from 'react';
import { 
  BarChart, Bar, 
  LineChart, Line, 
  PieChart, Pie,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid, Legend
} from 'recharts';

// --- FUNÇÕES E COMPONENTES AUXILIARES (sem alteração) ---
const formatCurrency = (value) => {
  if (value === null || value === undefined) return "R$ 0,00";
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
};

const CustomTooltip = ({ active, payload, y_axis_label }) => {
  if (active && payload && payload.length) {
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

const CustomPieTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="custom-tooltip">
        <p className="label">{data.name}</p>
        <p className="intro">{`Valor: ${new Intl.NumberFormat('pt-BR').format(data.value)}`}</p>
        <p className="intro">{`Percentual: ${(payload[0].percent * 100).toFixed(1)}%`}</p>
      </div>
    );
  }
  return null;
};


// --- COMPONENTE PRINCIPAL ---
function ChartComponent({ chartData }) {
  const { title, data, x_axis, y_axis, y_axis_label, chart_type } = chartData;
  
  // Define a cor única para o preenchimento e uma cor ligeiramente mais escura para a borda
  const BAR_FILL_COLOR = 'var(--text-secondary)'; // Cinza claro
  const BAR_STROKE_COLOR = '#667587'; // Um tom de cinza um pouco mais escuro
  
  const PIE_COLORS = ['#5e72e4', '#2dce89', '#ff8d4e', '#f5365c', '#11cdef', '#fb6340', '#ffd600'];

  const renderChart = () => {
    const yAxisKey = y_axis ? y_axis[0] : 'value';
    const xAxisKey = x_axis || 'name';
    const yAxisLabel = y_axis_label || yAxisKey;
    
    const processedData = data.map(item => ({
        ...item,
        name: item[xAxisKey],
        value: item[yAxisKey]
    }));

    const legendPayload = [
        { value: `Eixo Y: ${yAxisLabel}`, type: 'square', color: BAR_FILL_COLOR },
        { value: `Eixo X: ${xAxisKey.replace(/_/g, ' ')}`, type: 'square', color: 'var(--text-secondary)' }
    ];

    switch (chart_type) {
      case 'line':
      case 'bar':
      default:
        const Chart = chart_type === 'line' ? LineChart : BarChart;
        const ChartElement = chart_type === 'line' ? Line : Bar;
        
        return (
          <ResponsiveContainer width="100%" height={300}>
            <Chart data={processedData} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
              {/* GRADE DE FUNDO DE VOLTA */}
              <CartesianGrid strokeDasharray="3 3" stroke={"var(--border-color)"} />
              <XAxis dataKey="name" stroke="var(--text-secondary)" tick={{ fontSize: 11 }} />
              <YAxis stroke="var(--text-secondary)" />
              <Tooltip content={<CustomTooltip y_axis_label={yAxisLabel} />} cursor={{ fill: 'var(--primary-light)' }} />
              <Legend verticalAlign="top" payload={legendPayload} wrapperStyle={{ paddingBottom: '20px' }} />
              <ChartElement dataKey="value" name={yAxisLabel} radius={[4, 4, 0, 0]}>
                  {processedData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={BAR_FILL_COLOR}
                        stroke={BAR_STROKE_COLOR}
                        strokeWidth={1}
                      />
                  ))}
              </ChartElement>
            </Chart>
          </ResponsiveContainer>
        );

      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={processedData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius="80%" labelLine={false} label={false}>
                {processedData.map((entry, index) => (
                    <Cell 
                        key={`cell-${index}`} 
                        fill={PIE_COLORS[index % PIE_COLORS.length]} 
                        stroke={'var(--surface)'}
                        strokeWidth={2}
                    />
                ))}
              </Pie>
              <Tooltip content={<CustomPieTooltip />} />
              <Legend wrapperStyle={{ paddingTop: '20px' }} /> 
            </PieChart>
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