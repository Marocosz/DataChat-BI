// =================================================================================================
// =================================================================================================
//
//                       COMPONENTE DE VISUALIZAÇÃO DE GRÁFICOS
//
// Visão Geral do Componente:
//
// Este arquivo define um componente React reutilizável, `ChartComponent`, responsável por
// renderizar diferentes tipos de gráficos (barras, linhas, pizza) com base nos dados
// fornecidos pelo backend.
//
// Principais Funcionalidades:
//
// 1. Renderização Dinâmica: Utiliza uma estrutura `switch` para escolher qual tipo de
//    gráfico da biblioteca `recharts` será renderizado (`BarChart`, `LineChart`, `PieChart`),
//    com base na propriedade `chart_type` recebida.
//
// 2. Processamento de Dados: Mapeia os dados brutos recebidos do backend para um formato
//    padrão (`{ name, value }`) que a biblioteca `recharts` consegue entender facilmente,
//    tornando o componente flexível a diferentes nomes de campos (`x_axis`, `y_axis`).
//
// 3. Tooltips Personalizados: Implementa componentes de `Tooltip` customizados para
//    melhorar a experiência do usuário, exibindo informações claras e formatadas
//    quando o usuário interage com os gráficos.
//
// 4. Design Responsivo: Usa o `ResponsiveContainer` do `recharts` para garantir que os
//    gráficos se ajustem adequadamente ao tamanho do container onde são inseridos.
//
// 5. Estilização Centralizada: Define paletas de cores e estilos consistentes para
//    todos os gráficos, garantindo uma identidade visual coesa.
//
// =================================================================================================
// =================================================================================================

import React from 'react';
// Importa todos os componentes necessários da biblioteca de gráficos `recharts`.
import { 
  BarChart, Bar, 
  LineChart, Line, 
  PieChart, Pie,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid, Legend
} from 'recharts';

// --- Funções e Componentes Auxiliares ---

// Componente de Tooltip (dica de ferramenta) personalizado para os gráficos de Barra e Linha.
const CustomTooltip = ({ active, payload, y_axis_label }) => {
  // `active` é um booleano que indica se o tooltip deve ser exibido.
  // `payload` é um array com os dados do ponto/barra em que o mouse está.
  if (active && payload && payload.length) {
    // `payload[0].payload` contém o objeto de dados original para aquele ponto.
    const fullLabel = payload[0].payload.name;
    return (
      <div className="custom-tooltip">
        <p className="label">{`${fullLabel}`}</p>
        {/* Formata o valor numérico para exibição clara. */}
        <p className="intro">{`${y_axis_label || 'Valor'}: ${new Intl.NumberFormat('pt-BR').format(payload[0].value)}`}</p>
      </div>
    );
  }
  return null;
};

// Componente de Tooltip personalizado especificamente para o gráfico de Pizza.
const CustomPieTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="custom-tooltip">
        <p className="label">{data.name}</p>
        <p className="intro">{`Valor: ${new Intl.NumberFormat('pt-BR').format(data.value)}`}</p>
        {/* Calcula e exibe o percentual da fatia da pizza. */}
        <p className="intro">{`Percentual: ${(payload[0].percent * 100).toFixed(1)}%`}</p>
      </div>
    );
  }
  return null;
};


// --- Componente Principal ---

function ChartComponent({ chartData }) {
  // Desestrutura as propriedades recebidas do backend para fácil acesso.
  const { title, data, x_axis, y_axis, y_axis_label, chart_type } = chartData;
  
  // Define paletas de cores para os gráficos, usando variáveis CSS para consistência de tema.
  const BAR_FILL_COLOR = 'var(--text-secondary)';
  const BAR_STROKE_COLOR = '#667587';
  const PIE_COLORS = ['#5e72e4', '#2dce89', '#ff8d4e', '#f5365c', '#11cdef', '#fb6340', '#ffd600'];

  // Função principal que contém a lógica para renderizar o gráfico correto.
  const renderChart = () => {
    // Define as chaves dos eixos com base nos dados recebidos, com valores padrão para flexibilidade.
    const yAxisKey = y_axis ? y_axis[0] : 'value';
    const xAxisKey = x_axis || 'name';
    const yAxisLabel = y_axis_label || yAxisKey;
    
    // Processa os dados brutos, mapeando as chaves dinâmicas (ex: 'uf_destino', 'total_frete')
    // para chaves padronizadas (`name`, `value`) que o `recharts` usa.
    const processedData = data.map(item => ({
        ...item,
        name: item[xAxisKey],
        value: item[yAxisKey]
    }));

    // Cria o conteúdo da legenda para os gráficos de barra/linha.
    const legendPayload = [
        { value: `Eixo Y: ${yAxisLabel}`, type: 'square', color: BAR_FILL_COLOR },
        { value: `Eixo X: ${xAxisKey.replace(/_/g, ' ')}`, type: 'square', color: 'var(--text-secondary)' }
    ];

    // Estrutura `switch` para selecionar o tipo de gráfico a ser renderizado.
    switch (chart_type) {
      case 'line':
      case 'bar':
      default: // Se o tipo não for especificado, renderiza um gráfico de barras por padrão.
        // Define dinamicamente qual componente de gráfico e elemento usar.
        const Chart = chart_type === 'line' ? LineChart : BarChart;
        const ChartElement = chart_type === 'line' ? Line : Bar;
        
        return (
          // O `ResponsiveContainer` faz com que o gráfico ocupe todo o espaço do seu container pai.
          <ResponsiveContainer width="100%" height={300}>
            <Chart data={processedData} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
              {/* Renderiza a grade de fundo do gráfico para melhor legibilidade. */}
              <CartesianGrid strokeDasharray="3 3" stroke={"var(--border-color)"} />
              {/* Define o eixo X, usando a chave `name` dos dados processados. */}
              <XAxis dataKey="name" stroke="var(--text-secondary)" tick={{ fontSize: 11 }} />
              {/* Define o eixo Y. */}
              <YAxis stroke="var(--text-secondary)" />
              {/* Ativa o tooltip personalizado. */}
              <Tooltip content={<CustomTooltip y_axis_label={yAxisLabel} />} cursor={{ fill: 'var(--primary-light)' }} />
              {/* Renderiza a legenda customizada. */}
              <Legend verticalAlign="top" payload={legendPayload} wrapperStyle={{ paddingBottom: '20px' }} />
              {/* Renderiza o elemento principal do gráfico (barras ou linha). */}
              <ChartElement dataKey="value" name={yAxisLabel} radius={[4, 4, 0, 0]}>
                  {/* Mapeia os dados para criar uma "Célula" para cada barra, permitindo estilização individual (aqui, todas iguais). */}
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
              {/* Define o componente Pie (pizza), especificando as chaves de dados e nome. */}
              <Pie data={processedData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius="80%" labelLine={false} label={false}>
                {/* Mapeia os dados para criar uma "Célula" para cada fatia, aplicando cores diferentes. */}
                {processedData.map((entry, index) => (
                    <Cell 
                        key={`cell-${index}`} 
                        fill={PIE_COLORS[index % PIE_COLORS.length]} // Usa o operador de módulo para ciclar pelas cores.
                        stroke={'var(--surface)'}
                        strokeWidth={2}
                    />
                ))}
              </Pie>
              {/* Ativa o tooltip e a legenda específicos para o gráfico de pizza. */}
              <Tooltip content={<CustomPieTooltip />} />
              <Legend wrapperStyle={{ paddingTop: '20px' }} /> 
            </PieChart>
          </ResponsiveContainer>
        );
    }
  };

  // JSX final do componente.
  return (
    <div className="chart-container">
      {/* Exibe o título do gráfico recebido do backend. */}
      <h4>{title}</h4>
      {/* Chama a função que renderiza o gráfico apropriado. */}
      {renderChart()}
    </div>
  );
}

export default ChartComponent;