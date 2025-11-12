import { Select } from 'antd';
import type { StrategyParameter } from '@/types';

interface SelectParameterInputProps {
  parameter: StrategyParameter;
  value?: any;
  onChange?: (value: any) => void;
}

export default function SelectParameterInput({
  parameter,
  value,
  onChange,
}: SelectParameterInputProps) {
  if (!parameter.options || parameter.options.length === 0) {
    return <div>无可选项</div>;
  }

  return (
    <Select
      value={value}
      onChange={onChange}
      placeholder={`请选择${parameter.label}`}
    >
      {parameter.options.map((opt) => (
        <Select.Option key={opt.value} value={opt.value}>
          {opt.label}
        </Select.Option>
      ))}
    </Select>
  );
}
