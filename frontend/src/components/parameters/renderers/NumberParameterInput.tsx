import { InputNumber } from 'antd';
import type { StrategyParameter } from '@/types';

interface NumberParameterInputProps {
  parameter: StrategyParameter;
  value?: number;
  onChange?: (value: number | null) => void;
}

export default function NumberParameterInput({
  parameter,
  value,
  onChange,
}: NumberParameterInputProps) {
  return (
    <InputNumber
      style={{ width: '100%' }}
      value={value}
      onChange={onChange}
      min={parameter.min}
      max={parameter.max}
      step={parameter.type === 'integer' ? 1 : 0.1}
      precision={parameter.type === 'integer' ? 0 : 2}
    />
  );
}
