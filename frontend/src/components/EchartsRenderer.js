import ReactECharts from 'echarts-for-react';

const EchartsRenderer = ({ option }) => {
  return (
    <div className="chart-container">
      <ReactECharts
        option={option}
        style={{ height: '420px', width: '100%' }}
        opts={{ renderer: 'svg' }}
      />
    </div>
  );
};

export default EchartsRenderer;