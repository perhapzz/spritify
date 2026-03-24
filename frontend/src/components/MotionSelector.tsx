import type { Motion } from '../api';

interface MotionSelectorProps {
  motions: Motion[];
  selected: string;
  onSelect: (motionId: string) => void;
}

export function MotionSelector({
  motions,
  selected,
  onSelect,
}: MotionSelectorProps) {
  return (
    <div className="w-full">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Select Motion
      </label>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {motions.map((motion) => (
          <button
            key={motion.id}
            onClick={() => onSelect(motion.id)}
            className={`
              p-4 rounded-lg border-2 transition-all duration-200
              ${
                selected === motion.id
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 hover:border-gray-300 text-gray-700'
              }
            `}
          >
            <div className="font-medium">{motion.name}</div>
            <div className="text-xs text-gray-500 mt-1">{motion.description}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
