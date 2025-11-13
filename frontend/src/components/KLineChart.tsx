import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { KLine, RiskEvent } from '@/types';

interface KLineChartProps {
  data: KLine[];
  buyPoints?: Array<{ date: string; price: number }>;
  sellPoints?: Array<{ date: string; price: number }>;
  riskEvents?: RiskEvent[];  // 新增：风控事件
  height?: number;
}

export default function KLineChart({ data, buyPoints = [], sellPoints = [], riskEvents = [], height = 500 }: KLineChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current || data.length === 0) return;

    // Initialize chart
    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current);
    }

    const chart = chartInstance.current;

    // Prepare data
    const dates = data.map(item => item.date);
    const klineData = data.map(item => [item.open, item.close, item.low, item.high]);
    const volumes = data.map(item => item.volume);

    // Prepare buy/sell markers (strategy signals)
    const buyMarkers = buyPoints.map(point => ({
      coord: [point.date, point.price],
      value: '买',
      itemStyle: { color: '#52c41a' },
      symbolSize: 60,
    }));

    const sellMarkers = sellPoints.map(point => ({
      coord: [point.date, point.price],
      value: '卖',
      itemStyle: { color: '#1890ff' },
      symbolSize: 60,
    }));

    // Prepare risk event markers
    const riskEventMarkers = riskEvents.map(event => {
      const config: Record<string, { symbol: string; color: string; label: string }> = {
        stop_loss: { symbol: 'pin', color: '#fa8c16', label: '止损' },
        stop_profit: { symbol: 'pin', color: '#faad14', label: '止盈' },
        drawdown_protection: { symbol: 'pin', color: '#f5222d', label: '回撤' },
        rejected_order: { symbol: 'circle', color: '#d9d9d9', label: '拒绝' },
      };

      const eventConfig = config[event.type] || config.rejected_order;

      return {
        coord: [event.date, event.price || 0],
        value: eventConfig.label,
        symbol: eventConfig.symbol,
        itemStyle: { color: eventConfig.color },
        symbolSize: 50,
        label: {
          show: true,
          formatter: eventConfig.label,
          color: '#fff',
          fontSize: 10,
        },
      };
    });

    // Chart options
    const option = {
      animation: false,
      backgroundColor: '#fff',
      legend: {
        data: ['K线', '成交量'],
        top: 10,
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
        formatter: (params: any) => {
          const data = params[0];
          if (!data) return '';

          const kline = klineData[data.dataIndex];
          const volume = volumes[data.dataIndex];

          return `
            日期: ${dates[data.dataIndex]}<br/>
            开盘: ${kline[0].toFixed(2)}<br/>
            收盘: ${kline[1].toFixed(2)}<br/>
            最低: ${kline[2].toFixed(2)}<br/>
            最高: ${kline[3].toFixed(2)}<br/>
            成交量: ${volume.toLocaleString()}
          `;
        },
      },
      grid: [
        {
          left: '10%',
          right: '8%',
          top: '10%',
          height: '60%',
        },
        {
          left: '10%',
          right: '8%',
          top: '75%',
          height: '15%',
        },
      ],
      xAxis: [
        {
          type: 'category',
          data: dates,
          scale: true,
          boundaryGap: true,
          axisLine: { onZero: false },
          splitLine: { show: false },
          min: 'dataMin',
          max: 'dataMax',
        },
        {
          type: 'category',
          gridIndex: 1,
          data: dates,
          scale: true,
          boundaryGap: true,
          axisLine: { onZero: false },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { show: false },
          min: 'dataMin',
          max: 'dataMax',
        },
      ],
      yAxis: [
        {
          scale: true,
          splitArea: {
            show: true,
          },
        },
        {
          scale: true,
          gridIndex: 1,
          splitNumber: 2,
          axisLabel: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { show: false },
        },
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1],
          start: 0,
          end: 100,
        },
        {
          show: true,
          xAxisIndex: [0, 1],
          type: 'slider',
          top: '93%',
          start: 0,
          end: 100,
        },
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: klineData,
          itemStyle: {
            color: '#ef5350',
            color0: '#26a69a',
            borderColor: '#ef5350',
            borderColor0: '#26a69a',
          },
          markPoint: {
            label: {
              formatter: (param: any) => param.value,
            },
            data: [...buyMarkers, ...sellMarkers, ...riskEventMarkers],
          },
        },
        {
          name: '成交量',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: volumes,
          itemStyle: {
            color: (params: any) => {
              const kline = klineData[params.dataIndex];
              return kline[1] >= kline[0] ? '#ef5350' : '#26a69a';
            },
          },
        },
      ],
    };

    chart.setOption(option);

    // Handle resize
    const handleResize = () => {
      chart.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [data, buyPoints, sellPoints, riskEvents]);

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
