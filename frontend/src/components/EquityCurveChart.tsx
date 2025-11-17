import { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { Switch } from 'antd';
import type { EquityPoint } from '@/types';
import { formatCurrency } from '@/utils/format';

interface EquityCurveChartProps {
  data: EquityPoint[];
  initialCapital: number;
  comparisonData?: EquityPoint[];  // 对比数据（无风控）
  benchmarkData?: EquityPoint[];   // 新增：基准数据
  benchmarkName?: string;          // 新增：基准名称
  height?: number;
}

export default function EquityCurveChart({
  data,
  initialCapital,
  comparisonData,
  benchmarkData,
  benchmarkName = '基准指数',
  height = 300
}: EquityCurveChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const [showComparison, setShowComparison] = useState(true);
  const [showBenchmark, setShowBenchmark] = useState(true);

  useEffect(() => {
    if (!chartRef.current || data.length === 0) return;

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current);
    }

    const chart = chartInstance.current;

    const dates = data.map(item => item.date);
    const equityData = data.map(item => item.equity);
    const capitalData = data.map(() => initialCapital);  // 改名避免冲突

    // Prepare comparison data if available
    const comparisonEquityData = comparisonData && showComparison
      ? comparisonData.map(item => item.equity)
      : [];

    // Prepare benchmark data if available
    const benchmarkEquityData = benchmarkData && showBenchmark
      ? benchmarkData.map(item => item.equity)
      : [];

    // Build legend data
    const legendData = ['策略资产', '本金'];
    if (comparisonData && showComparison) {
      legendData.push('无风控资产');
    }
    if (benchmarkData && showBenchmark) {
      legendData.push(benchmarkName);
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
            if (param.seriesName === '策略资产') {
              result += `策略资产: ${formatCurrency(param.value)}<br/>`;
            } else if (param.seriesName === '无风控资产') {
              result += `无风控: ${formatCurrency(param.value)}<br/>`;
            } else if (param.seriesName === '本金') {
              result += `本金: ${formatCurrency(param.value)}<br/>`;
            } else if (param.seriesName === benchmarkName) {
              result += `${benchmarkName}: ${formatCurrency(param.value)}<br/>`;
            }
          });

          // Calculate returns comparison
          const strategyPoint = params.find((p: any) => p.seriesName === '策略资产');
          if (strategyPoint) {
            const strategyReturn = ((strategyPoint.value - initialCapital) / initialCapital * 100).toFixed(2);
            result += `<br/>策略收益率: ${strategyReturn}%`;

            // If benchmark exists, show comparison
            const benchmarkPoint = params.find((p: any) => p.seriesName === benchmarkName);
            if (benchmarkPoint && showBenchmark) {
              const benchmarkReturn = ((benchmarkPoint.value - initialCapital) / initialCapital * 100).toFixed(2);
              result += `<br/>${benchmarkName}收益率: ${benchmarkReturn}%`;
              const diff = parseFloat(strategyReturn) - parseFloat(benchmarkReturn);
              result += `<br/>超额收益: ${diff >= 0 ? '+' : ''}${diff.toFixed(2)}%`;
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
          name: '策略资产',
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
          data: capitalData,  // 使用新的变量名
          lineStyle: {
            type: 'dashed',
            color: '#bfbfbf',
            width: 1,
          },
        },
        ...(comparisonData && showComparison
          ? [
              {
                name: '无风控资产',
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
        ...(benchmarkData && showBenchmark
          ? [
              {
                name: benchmarkName,
                type: 'line',
                data: benchmarkEquityData,
                smooth: true,
                lineStyle: {
                  width: 2,
                  color: '#52c41a',
                },
                itemStyle: {
                  color: '#52c41a',
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
  }, [data, initialCapital, comparisonData, benchmarkData, benchmarkName, showComparison, showBenchmark]);

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
      {(comparisonData || benchmarkData) && (
        <div style={{ position: 'absolute', top: 10, right: 10, zIndex: 10, display: 'flex', gap: 8 }}>
          {comparisonData && (
            <Switch
              checked={showComparison}
              onChange={setShowComparison}
              checkedChildren="显示对比"
              unCheckedChildren="隐藏对比"
            />
          )}
          {benchmarkData && (
            <Switch
              checked={showBenchmark}
              onChange={setShowBenchmark}
              checkedChildren="显示基准"
              unCheckedChildren="隐藏基准"
            />
          )}
        </div>
      )}
      <div ref={chartRef} style={{ width: '100%', height: `${height}px` }} />
    </div>
  );
}
