import type { Mode } from '../api';

interface GenerationProgressProps {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  mode: Mode;
  error?: string;
}

interface Step {
  label: string;
  range: [number, number]; // [start%, end%]
}

const AI_STEPS: Step[] = [
  { label: '🎨 生成三视图', range: [10, 30] },
  { label: '🏃 生成动作帧', range: [30, 80] },
  { label: '🧩 合成精灵表', range: [80, 100] },
];

const CLASSIC_STEPS: Step[] = [
  { label: '⚙️ 生成动画帧', range: [10, 70] },
  { label: '🧩 合成精灵表', range: [70, 100] },
];

function getCurrentStep(steps: Step[], progress: number): number {
  for (let i = steps.length - 1; i >= 0; i--) {
    if (progress >= steps[i].range[0]) return i;
  }
  return 0;
}

export function GenerationProgress({
  status,
  progress,
  mode,
  error,
}: GenerationProgressProps) {
  const steps = mode === 'ai' ? AI_STEPS : CLASSIC_STEPS;
  const currentStep = getCurrentStep(steps, progress);

  return (
    <div className="w-full space-y-4">
      {/* Step indicators */}
      <div className="flex justify-between">
        {steps.map((step, i) => (
          <div
            key={i}
            className={`flex items-center gap-1.5 text-sm ${
              i < currentStep
                ? 'text-green-600'
                : i === currentStep
                ? 'text-blue-600 font-medium'
                : 'text-gray-400'
            }`}
          >
            <span
              className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                i < currentStep
                  ? 'bg-green-500 text-white'
                  : i === currentStep
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-500'
              }`}
            >
              {i < currentStep ? '✓' : i + 1}
            </span>
            <span className="hidden sm:inline">{step.label}</span>
          </div>
        ))}
      </div>

      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full transition-all duration-500 rounded-full ${
            status === 'failed'
              ? 'bg-red-500'
              : status === 'completed'
              ? 'bg-green-500'
              : 'bg-blue-500'
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Status text */}
      <div className="flex justify-between text-sm">
        <span className="text-gray-600">
          {status === 'failed'
            ? '生成失败'
            : status === 'completed'
            ? '完成！'
            : steps[currentStep]?.label || '处理中...'}
        </span>
        <span className="text-gray-500">{progress}%</span>
      </div>

      {error && <p className="text-red-500 text-sm">{error}</p>}
    </div>
  );
}
