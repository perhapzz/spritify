import type { Mode } from '../api';

interface ModeSelectorProps {
  selected: Mode;
  onSelect: (mode: Mode) => void;
}

const MODES = [
  {
    id: 'ai' as Mode,
    name: 'AI HD',
    icon: '⚡',
    description: 'AI 生成多视角，高质量角色一致性',
    badge: '推荐',
    badgeColor: 'bg-blue-500',
  },
  {
    id: 'classic' as Mode,
    name: 'Classic',
    icon: '🚀',
    description: '骨骼变形动画，快速生成',
    badge: '快速',
    badgeColor: 'bg-gray-400',
  },
];

export function ModeSelector({ selected, onSelect }: ModeSelectorProps) {
  return (
    <div className="grid grid-cols-2 gap-4">
      {MODES.map((mode) => (
        <button
          key={mode.id}
          onClick={() => onSelect(mode.id)}
          className={`
            relative p-5 rounded-xl border-2 transition-all text-left
            ${
              selected === mode.id
                ? 'border-blue-500 bg-blue-50 shadow-md'
                : 'border-gray-200 hover:border-gray-300 bg-white'
            }
          `}
        >
          {mode.badge && (
            <span
              className={`absolute -top-2 -right-2 ${mode.badgeColor} text-white text-xs px-2 py-0.5 rounded-full font-medium`}
            >
              {mode.badge}
            </span>
          )}
          <div className="text-2xl mb-2">{mode.icon}</div>
          <div className="font-semibold text-gray-800">{mode.name}</div>
          <div className="text-xs text-gray-500 mt-1">{mode.description}</div>
        </button>
      ))}
    </div>
  );
}
