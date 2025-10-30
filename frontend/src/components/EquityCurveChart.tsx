import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { EquityPoint } from '@/types';
import { formatCurrency } from '@/utils/format';

interface EquityCurveChartProps {
  data: EquityPoint[];
  initialCapital: number;
  height?: number;
}

export default function EquityCurveChart({ data, initialCapital, height = 300 }: EquityCurveChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current || data.length === 0) return;

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current);
    }

    const chart = chartInstance.current;

    const dates = data.map(item => item.date);
    const equityData = data.map(item => item.equity);
    const benchmarkData = data.map(() => initialCapital);

    const option = {
      backgroundColor: '#fff',
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
        formatter: (params: any) => {
          const equity = params[0];
          const benchmark = params[1];
          return `
            日期: ${dates[equity.dataIndex]}<br/>
            资产: ${formatCurrency(equity.value)}<br/>
            本金: ${formatCurrency(benchmark.value)}<br/>
            收益: ${formatCurrency(equity.value - benchmark.value)}
          `;
        },
      },
      legend: {
        data: ['资产曲线', '本金'],
        top: 10,
      },
      grid: {
        left: '10%',
        right: '8%',
        top: '15%',
        bottom: '15%',
      },
      xAxis: {
        type: 'category',
        data: dates,
        boundaryGap: false,
      },
      yAxis: {
        type: 'value',
        scale: true,
        axisLabel: {
          formatter: (value: number) => {
            if (value >= 10000) {
              return `${(value / 10000).toFixed(1)}万`;
            }
            return value.toFixed(0);
          },
        },
      },
      series: [
        {
          name: '资产曲线',
          type: 'line',
          data: equityData,
          smooth: true,
          lineStyle: {
            width: 2,
            color: '#1890ff',
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
              { offset: 1, color: 'rgba(24, 144, 255, 0.05)' },
            ]),
          },
        },
        {
          name: '本金',
          type: 'line',
          data: benchmarkData,
          lineStyle: {
            type: 'dashed',
            color: '#bfbfbf',
          },
        },
      ],
    };

    chart.setOption(option);

    const handleResize = () => {
      chart.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [data, initialCapital]);

  useEffect(() => {
    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose();
        chartInstance.current = null;
      }
    };
  }, []);

  return <div ref={chartRef} style={{ width: '100%', height: `${height}px` }} />;
}
