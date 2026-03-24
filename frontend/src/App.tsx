import { useState, useEffect, useCallback } from 'react';
import { ImageUploader } from './components/ImageUploader';
import { ModeSelector } from './components/ModeSelector';
import { TurnaroundPreview } from './components/TurnaroundPreview';
import { MotionSelector } from './components/MotionSelector';
import { GenerationProgress } from './components/GenerationProgress';
import { SpritePreview } from './components/SpritePreview';
import type { Mode, Motion, TaskStatus, TurnaroundResult } from './api';
import { getMotions, generateSprite, generateTurnaround, getDownloadUrl } from './api';

type Step = 'upload' | 'turnaround' | 'motion' | 'generating' | 'result';

const AI_MOTIONS: Motion[] = [
  { id: 'walk', name: 'Walk', description: '步行循环' },
  { id: 'run', name: 'Run', description: '跑步循环' },
  { id: 'idle', name: 'Idle', description: '待机呼吸' },
  { id: 'jump', name: 'Jump', description: '跳跃动作' },
];

const CLASSIC_MOTIONS: Motion[] = [
  { id: 'dab', name: 'Dab', description: 'Dab dance move' },
  { id: 'jumping', name: 'Jump', description: 'Jumping motion' },
  { id: 'wave_hello', name: 'Wave', description: 'Waving hello' },
  { id: 'zombie', name: 'Zombie', description: 'Zombie walk' },
  { id: 'jumping_jacks', name: 'Jumping Jacks', description: 'Exercise' },
  { id: 'jesse_dance', name: 'Dance', description: 'Dance routine' },
];

function App() {
  const [mode, setMode] = useState<Mode>('ai');
  const [step, setStep] = useState<Step>('upload');
  const [motions, setMotions] = useState<Motion[]>(AI_MOTIONS);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedMotion, setSelectedMotion] = useState<string>('walk');
  const [frameCount, setFrameCount] = useState(8);
  const [frameSize, setFrameSize] = useState(128);

  // Turnaround state
  const [turnaround, setTurnaround] = useState<TurnaroundResult | null>(null);
  const [turnaroundLoading, setTurnaroundLoading] = useState(false);
  const [turnaroundError, setTurnaroundError] = useState<string | null>(null);

  // Generation state
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);

  // Update motions when mode changes
  useEffect(() => {
    const defaults = mode === 'ai' ? AI_MOTIONS : CLASSIC_MOTIONS;
    setMotions(defaults);
    setSelectedMotion(defaults[0].id);

    getMotions(mode)
      .then(setMotions)
      .catch(() => setMotions(defaults));
  }, [mode]);

  const handleModeChange = useCallback((m: Mode) => {
    setMode(m);
    handleReset();
  }, []);

  const handleFileSelected = useCallback((file: File) => {
    setSelectedFile(file);
    setStep('upload');
    setTurnaround(null);
    setTurnaroundError(null);
    setTaskStatus(null);
  }, []);

  const handleUploadContinue = useCallback(async () => {
    if (!selectedFile) return;

    if (mode === 'ai') {
      // Generate turnaround
      setStep('turnaround');
      setTurnaroundLoading(true);
      setTurnaroundError(null);
      try {
        const result = await generateTurnaround(selectedFile);
        setTurnaround(result);
      } catch (e: any) {
        setTurnaroundError(e?.response?.data?.detail || '三视图生成失败');
      } finally {
        setTurnaroundLoading(false);
      }
    } else {
      setStep('motion');
    }
  }, [selectedFile, mode]);

  const handleTurnaroundRetry = useCallback(() => {
    handleUploadContinue();
  }, [handleUploadContinue]);

  const handleTurnaroundConfirm = useCallback(() => {
    setStep('motion');
  }, []);

  const handleGenerate = useCallback(async () => {
    if (!selectedFile) return;

    setStep('generating');
    setTaskStatus({ task_id: '', status: 'processing', progress: 10 });

    try {
      const result = await generateSprite(
        selectedFile,
        selectedMotion,
        frameCount,
        frameSize,
        mode
      );
      setTaskStatus(result);
      if (result.status === 'completed') {
        setStep('result');
      }
    } catch (e: any) {
      setTaskStatus({
        task_id: '',
        status: 'failed',
        error: e?.response?.data?.detail || '生成失败',
      });
    }
  }, [selectedFile, selectedMotion, frameCount, frameSize, mode]);

  const handleDownloadPng = useCallback(() => {
    if (!taskStatus?.task_id) return;
    window.open(getDownloadUrl(taskStatus.task_id), '_blank');
  }, [taskStatus]);

  const handleExportGif = useCallback((blob: Blob) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sprite_animation.gif';
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  const handleReset = useCallback(() => {
    setSelectedFile(null);
    setStep('upload');
    setTurnaround(null);
    setTurnaroundLoading(false);
    setTurnaroundError(null);
    setTaskStatus(null);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🎮 Spritify
          </h1>
          <p className="text-gray-600">
            Transform static images into animated sprite sheets
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8 space-y-8">
          {/* Mode Selector */}
          <section>
            <h2 className="text-lg font-semibold text-gray-700 mb-4">
              选择模式
            </h2>
            <ModeSelector selected={mode} onSelect={handleModeChange} />
          </section>

          {/* Step 1: Upload */}
          <section>
            <h2 className="text-lg font-semibold text-gray-700 mb-4">
              1. 上传角色图片
            </h2>
            {mode === 'ai' && (
              <p className="text-sm text-gray-500 mb-3">
                💡 上传角色正面图效果最佳
              </p>
            )}
            <ImageUploader onFileSelected={handleFileSelected} />

            {selectedFile && step === 'upload' && (
              <button
                onClick={handleUploadContinue}
                className="mt-4 w-full py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition"
              >
                继续 →
              </button>
            )}
          </section>

          {/* Step 2 (AI): Turnaround Preview */}
          {mode === 'ai' && (step === 'turnaround' || turnaround) && step !== 'upload' && (
            <section>
              <h2 className="text-lg font-semibold text-gray-700 mb-4">
                2. 三视图预览
              </h2>
              <TurnaroundPreview
                result={turnaround}
                isLoading={turnaroundLoading}
                error={turnaroundError}
                onConfirm={handleTurnaroundConfirm}
                onRetry={handleTurnaroundRetry}
              />
            </section>
          )}

          {/* Step: Select Motion */}
          {(step === 'motion' || step === 'generating' || step === 'result') && (
            <section>
              <h2 className="text-lg font-semibold text-gray-700 mb-4">
                {mode === 'ai' ? '3' : '2'}. 选择动作
              </h2>
              <MotionSelector
                motions={motions}
                selected={selectedMotion}
                onSelect={setSelectedMotion}
              />
            </section>
          )}

          {/* Step: Settings */}
          {(step === 'motion' || step === 'generating' || step === 'result') && (
            <section>
              <h2 className="text-lg font-semibold text-gray-700 mb-4">
                {mode === 'ai' ? '4' : '3'}. 设置
              </h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    帧数
                  </label>
                  <select
                    value={frameCount}
                    onChange={(e) => setFrameCount(Number(e.target.value))}
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {[4, 6, 8, 12, 16].map((n) => (
                      <option key={n} value={n}>
                        {n} 帧
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    帧尺寸
                  </label>
                  <select
                    value={frameSize}
                    onChange={(e) => setFrameSize(Number(e.target.value))}
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {[64, 128, 256, 512].map((n) => (
                      <option key={n} value={n}>
                        {n}×{n} px
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </section>
          )}

          {/* Generate Button */}
          {step === 'motion' && (
            <button
              onClick={handleGenerate}
              className="w-full py-4 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition"
            >
              🚀 生成 Sprite Sheet
            </button>
          )}

          {/* Progress */}
          {step === 'generating' && taskStatus && taskStatus.status !== 'completed' && (
            <GenerationProgress
              status={taskStatus.status}
              progress={taskStatus.progress || 0}
              mode={mode}
              error={taskStatus.error}
            />
          )}

          {/* Result */}
          {step === 'result' && taskStatus?.status === 'completed' && taskStatus.result_url && (
            <section className="space-y-6">
              <h2 className="text-lg font-semibold text-gray-700">
                🎉 你的 Sprite Sheet
              </h2>

              <div className="flex flex-col lg:flex-row gap-8 items-start">
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-gray-600 mb-3">
                    动画预览
                  </h3>
                  <SpritePreview
                    spriteUrl={taskStatus.result_url}
                    frameCount={frameCount}
                    frameSize={frameSize}
                    onExportGif={handleExportGif}
                  />
                </div>

                <div className="flex-1">
                  <h3 className="text-sm font-medium text-gray-600 mb-3">
                    完整 Sprite Sheet
                  </h3>
                  <img
                    src={taskStatus.result_url}
                    alt="Sprite Sheet"
                    className="border border-gray-200 rounded-lg max-w-full"
                    style={{ imageRendering: 'pixelated' }}
                  />
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={handleDownloadPng}
                  className="flex-1 py-3 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 transition"
                >
                  📥 下载 PNG
                </button>
                <button
                  onClick={() => {
                    document.querySelector<HTMLButtonElement>('[data-gif-export]')?.click();
                  }}
                  className="flex-1 py-3 bg-purple-600 text-white font-semibold rounded-xl hover:bg-purple-700 transition"
                >
                  🎬 下载 GIF
                </button>
                <button
                  onClick={handleReset}
                  className="flex-1 py-3 bg-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-300 transition"
                >
                  再来一个
                </button>
              </div>
            </section>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-gray-400 text-sm mt-8">
          Powered by AI + AnimatedDrawings
        </p>
      </div>
    </div>
  );
}

export default App;
