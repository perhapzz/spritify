interface GenerationProgressProps {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  error?: string;
}

export function GenerationProgress({
  status,
  progress,
  error,
}: GenerationProgressProps) {
  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-2">
        <span className="text-gray-600">
          {status === 'pending' && 'Waiting...'}
          {status === 'processing' && 'Generating sprite sheet...'}
          {status === 'completed' && 'Complete!'}
          {status === 'failed' && 'Failed'}
        </span>
        <span className="text-gray-500">{progress}%</span>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full transition-all duration-300 rounded-full ${
            status === 'failed'
              ? 'bg-red-500'
              : status === 'completed'
              ? 'bg-green-500'
              : 'bg-blue-500'
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>

      {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
    </div>
  );
}
