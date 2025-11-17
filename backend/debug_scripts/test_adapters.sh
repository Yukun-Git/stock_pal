#!/bin/bash

# 测试数据适配器系统

echo "======================================================"
echo "数据适配器系统测试"
echo "======================================================"

# 等待服务启动
echo ""
echo "等待backend服务启动..."
for i in {1..30}; do
    if curl -s http://localhost:4001/health > /dev/null 2>&1; then
        echo "✓ Backend服务已就绪"
        break
    fi
    echo "  等待中... ($i/30)"
    sleep 2
done

echo ""
echo "======================================================"
echo "测试1: YFinance适配器 - 港股数据 (小米集团 1810.HK)"
echo "======================================================"

curl -s "http://localhost:4001/api/v1/stocks/1810.HK/data?start_date=20251001&end_date=20251115" | \
    python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        print('✓ 成功获取数据')
        print(f\"  数据条数: {len(data['data'])}\")
        if data['data']:
            first = data['data'][0]
            last = data['data'][-1]
            print(f\"  日期范围: {first['date']} 到 {last['date']}\")
            print(f\"  最新收盘价: {last['close']:.2f} HKD\")
    else:
        print('✗ 获取失败:', data.get('error'))
except Exception as e:
    print('✗ 解析失败:', e)
"

echo ""
echo "======================================================"
echo "测试2: YFinance适配器 - A股数据 (贵州茅台 600519.SH)"
echo "======================================================"

curl -s "http://localhost:4001/api/v1/stocks/600519.SH/data?start_date=20251001&end_date=20251115" | \
    python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        print('✓ 成功获取数据')
        print(f\"  数据条数: {len(data['data'])}\")
        if data['data']:
            first = data['data'][0]
            last = data['data'][-1]
            print(f\"  日期范围: {first['date']} 到 {last['date']}\")
            print(f\"  最新收盘价: {last['close']:.2f} CNY\")
    else:
        print('✗ 获取失败:', data.get('error'))
except Exception as e:
    print('✗ 解析失败:', e)
"

echo ""
echo "======================================================"
echo "测试3: 检查配置的数据源"
echo "======================================================"

docker-compose logs backend 2>&1 | grep -i "adapter" | tail -5

echo ""
echo "======================================================"
echo "测试完成"
echo "======================================================"
