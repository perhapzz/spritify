import type { TurnaroundResult } from '../api';

interface TurnaroundPreviewProps {
  result: TurnaroundResult | null;
  isLoading: boolean;
  error: string | null;
  onConfirm: () => void;
  onRetry: () => void;
}

const VIEW_LABELS: Record<string, string> = {
  front: '正面',
  side: '侧面',
  back: '背面',
};

export function TurnaroundPreview({
  result,
  isLoading,
  error,
  onConfirm,
  onRetry,
}: TurnaroundPreviewProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center py-8">
        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-gray-600">生成三视图中...</p>
        <p className="text-gray-400 text-sm mt-1">AI 正在分析角色结构</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-6">
        <p className="text-red-500 mb-3">{error}</p>
        <button
          onClick={onRetry}
          className="px-6 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition"
        >
          重试
        </button>
      </div>
    );
  }

  if (!result) return null;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        {(['front', 'side', 'back'] as const).map((view) => (
          <div key={view} className="flex flex-col items-center">
            <div className="bg-gray-100 rounded-lg p-2 w-full aspect-square flex items-center justify-center overflow-hidden">
              <img
                src={result.views[view]}
                alt={`${view} view`}
                className="max-w-full max-h-full object-contain rounded"
              />
            </div>
            <span className="text-sm text-gray-600 mt-2 font-medium">
              {VIEW_LABELS[view] || view}
            </span>
          </div>
        ))}
      </div>

      <div className="flex gap-3 justify-center pt-2">
        <button
          onClick={onConfirm}
          className="px-8 py-2.5 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 transition"
        >
          确认，继续 →
        </button>
        <button
          onClick={onRetry}
          className="px-6 py-2.5 bg-gray-200 text-gray-700 rounded-xl hover:bg-gray-300 transition"
        >
          重新生成
        </button>
      </div>

      {result.provider === 'mock' && (
        <p className="text-center text-xs text-amber-500">
          ⚠️ Mock 模式 — 接入 AI 后将生成真实三视图
        </p>
      )}
    </div>
  );
}
