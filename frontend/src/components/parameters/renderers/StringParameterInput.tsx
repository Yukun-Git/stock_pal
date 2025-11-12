import { Input } from 'antd';
import type { StrategyParameter } from '@/types';

interface StringParameterInputProps {
  parameter: StrategyParameter;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export default function StringParameterInput({
  parameter,
  value,
  onChange,
}: StringParameterInputProps) {
  return (
    <Input
      value={value}
      onChange={onChange}
      placeholder={`请输入${parameter.label}`}
    />
  );
}
