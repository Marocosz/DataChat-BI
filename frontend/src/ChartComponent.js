import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const ChartComponent = ({ chartData }) => {
  const { title, data, x_axis, y_axis } = chartData;

  return (
    <div className="chart-container">
      <h4>{title}</h4>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={x_axis} stroke="#ccc" />
          <YAxis stroke="#ccc" />
          <Tooltip 
            contentStyle={{ backgroundColor: '#282c34', border: '1px solid #555' }} 
            labelStyle={{ color: '#fff' }}
          />
          <Legend />
          {y_axis.map((key, index) => (
             <Bar key={index} dataKey={key} fill={index % 2 === 0 ? '#8884d8' : '#82ca9d'} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ChartComponent;