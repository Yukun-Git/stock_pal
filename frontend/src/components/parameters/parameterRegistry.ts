import { ComponentType } from 'react';
import type { StrategyParameter } from '@/types';
import {
  NumberParameterInput,
  BooleanParameterInput,
  SelectParameterInput,
  StringParameterInput,
} from './renderers';

export interface ParameterInputProps {
  parameter: StrategyParameter;
  value?: any;
  onChange?: (value: any) => void;
  checked?: boolean; // For boolean type
}

type ParameterRenderer = ComponentType<ParameterInputProps>;

/**
 * Parameter Registry - Maps parameter types to their corresponding input components
 *
 * Similar to backend's StrategyRegistry, this allows adding new parameter types
 * without modifying the BacktestPage component.
 */
class ParameterRegistry {
  private renderers: Map<string, ParameterRenderer> = new Map();

  constructor() {
    // Register default renderers
    this.register('integer', NumberParameterInput);
    this.register('float', NumberParameterInput);
    this.register('boolean', BooleanParameterInput);
    this.register('select', SelectParameterInput);
    this.register('string', StringParameterInput);
  }

  /**
   * Register a new parameter type renderer
   * @param type - Parameter type identifier
   * @param renderer - React component to render this type
   */
  register(type: string, renderer: ParameterRenderer): void {
    this.renderers.set(type, renderer);
  }

  /**
   * Get renderer for a specific parameter type
   * @param type - Parameter type identifier
   * @returns Renderer component or undefined if not found
   */
  getRenderer(type: string): ParameterRenderer | undefined {
    return this.renderers.get(type);
  }

  /**
   * Check if a renderer exists for a parameter type
   * @param type - Parameter type identifier
   * @returns true if renderer exists
   */
  hasRenderer(type: string): boolean {
    return this.renderers.has(type);
  }

  /**
   * Get all registered parameter types
   * @returns Array of registered type identifiers
   */
  getRegisteredTypes(): string[] {
    return Array.from(this.renderers.keys());
  }
}

// Export singleton instance
export const parameterRegistry = new ParameterRegistry();
