import { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { Switch } from 'antd';
import type { EquityPoint } from '@/types';
import { formatCurrency } from '@/utils/format';

interface EquityCurveChartProps {
  data: EquityPoint[];
  initialCapital: number;
  comparisonData?: EquityPoint[];  // 新增：对比数据（无风控）
  height?: number;
}

export default function EquityCurveChart({ data, initialCapital, comparisonData, height = 300 }: EquityCurveChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const [showComparison, setShowComparison] = useState(true);

  useEffect(() => {
    if (!chartRef.current || data.length === 0) return;

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current);
    }

    const chart = chartInstance.current;

    const dates = data.map(item => item.date);
    const equityData = data.map(item => item.equity);
    const benchmarkData = data.map(() => initialCapital);

    // Prepare comparison data if available
    const comparisonEquityData = comparisonData && showComparison
      ? comparisonData.map(item => item.equity)
      : [];

    // Build legend data
    const legendData = ['资产曲线（有风控）', '本金'];
    if (comparisonData && showComparison) {
      legendData.push('资产曲线（无风控）');
    }

    const option = {
      backgroundColor: '#fff',
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
        formatter: (params: any) => {
          let result = `日期: ${dates[params[0].dataIndex]}<br/>`;

          params.forEach((param: any) => {
            if (param.seriesName === '资产曲线（有风控）') {
              result += `有风控: ${formatCurrency(param.value)}<br/>`;
            } else if (param.seriesName === '资产曲线（无风控）') {
              result += `无风控: ${formatCurrency(param.value)}<br/>`;
            } else if (param.seriesName === '本金') {
              result += `本金: ${formatCurrency(param.value)}<br/>`;
            }
          });

          // Calculate difference if comparison data exists
          if (params.length >= 2 && comparisonData && showComparison) {
            const withRisk = params.find((p: any) => p.seriesName === '资产曲线（有风控）');
            const withoutRisk = params.find((p: any) => p.seriesName === '资产曲线（无风控）');
            if (withRisk && withoutRisk) {
              const diff = withRisk.value - withoutRisk.value;
              result += `<br/>差异: ${formatCurrency(diff)} (${diff >= 0 ? '+' : ''}${((diff / withoutRisk.value) * 100).toFixed(2)}%)`;
            }
          }

          return result;
        },
      },
      legend: {
        data: legendData,
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
          name: '资产曲线（有风控）',
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
            width: 1,
          },
        },
        ...(comparisonData && showComparison
          ? [
              {
                name: '资产曲线（无风控）',
                type: 'line',
                data: comparisonEquityData,
                smooth: true,
                lineStyle: {
                  width: 2,
                  type: 'dashed' as const,
                  color: '#ff7875',
                },
              },
            ]
          : []),
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
  }, [data, initialCapital, comparisonData, showComparison]);

  useEffect(() => {
    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose();
        chartInstance.current = null;
      }
    };
  }, []);

  return (
    <div style={{ position: 'relative' }}>
      {comparisonData && (
        <div style={{ position: 'absolute', top: 10, right: 10, zIndex: 10 }}>
          <Switch
            checked={showComparison}
            onChange={setShowComparison}
            checkedChildren="显示对比"
            unCheckedChildren="隐藏对比"
          />
        </div>
      )}
      <div ref={chartRef} style={{ width: '100%', height: `${height}px` }} />
    </div>
  );
}
