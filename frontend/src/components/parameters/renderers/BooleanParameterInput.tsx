import { Switch } from 'antd';
import type { StrategyParameter } from '@/types';

interface BooleanParameterInputProps {
  parameter: StrategyParameter;
  checked?: boolean;
  onChange?: (checked: boolean) => void;
}

export default function BooleanParameterInput({
  checked,
  onChange,
}: BooleanParameterInputProps) {
  return (
    <Switch
      checked={checked}
      onChange={onChange}
      checkedChildren="是"
      unCheckedChildren="否"
    />
  );
}
