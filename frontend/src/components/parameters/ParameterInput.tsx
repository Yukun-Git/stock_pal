import { parameterRegistry } from './parameterRegistry';
import type { StrategyParameter } from '@/types';

interface ParameterInputProps {
  parameter: StrategyParameter;
  value?: any;
  onChange?: (value: any) => void;
}

/**
 * ParameterInput - Main entry point for parameter input components
 *
 * This component automatically selects the appropriate input component based on
 * the parameter type using the parameter registry. This eliminates the need for
 * hardcoded if-else chains in the BacktestPage.
 *
 * Similar to backend's SignalAnalysisService refactoring, this uses a registry
 * pattern to delegate rendering to specialized components.
 *
 * @example
 * // Before refactoring (34 lines of hardcoded logic):
 * if (param.type === 'select' && param.options) {
 *   inputComponent = <Select>...</Select>;
 * } else if (param.type === 'boolean') {
 *   inputComponent = <Switch>...</Switch>;
 * } else {
 *   inputComponent = <InputNumber>...</InputNumber>;
 * }
 *
 * // After refactoring (1 line):
 * <ParameterInput parameter={param} />
 */
export default function ParameterInput({ parameter, value, onChange }: ParameterInputProps) {
  // Get renderer from registry based on parameter type
  const Renderer = parameterRegistry.getRenderer(parameter.type);

  if (!Renderer) {
    console.warn(`No renderer found for parameter type: ${parameter.type}`);
    return (
      <div style={{ color: '#ff4d4f', padding: '8px 12px', backgroundColor: '#fff2e8', borderRadius: 4 }}>
        不支持的参数类型: {parameter.type}
      </div>
    );
  }

  // Render using the registered component
  // For boolean type, use 'checked' prop instead of 'value'
  if (parameter.type === 'boolean') {
    return <Renderer parameter={parameter} checked={value} onChange={onChange} />;
  }

  return <Renderer parameter={parameter} value={value} onChange={onChange} />;
}
