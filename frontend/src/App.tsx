import { useState, useEffect, useCallback } from 'react';
import { ImageUploader } from './components/ImageUploader';
import { MotionSelector } from './components/MotionSelector';
import { GenerationProgress } from './components/GenerationProgress';
import { SpritePreview } from './components/SpritePreview';
import type { Motion, TaskStatus } from './api';
import { getMotions, generateSprite, getTaskStatus, getDownloadUrl } from './api';

const DEFAULT_MOTIONS: Motion[] = [
  { id: 'dab', name: 'Dab', description: 'Dab dance move' },
  { id: 'jumping', name: 'Jump', description: 'Jumping motion' },
  { id: 'wave_hello', name: 'Wave', description: 'Waving hello' },
  { id: 'zombie', name: 'Zombie', description: 'Zombie walk' },
  { id: 'jumping_jacks', name: 'Jumping Jacks', description: 'Exercise' },
  { id: 'jesse_dance', name: 'Dance', description: 'Dance routine' },
];

function App() {
  const [motions, setMotions] = useState<Motion[]>(DEFAULT_MOTIONS);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedMotion, setSelectedMotion] = useState<string>('dab');
  const [frameCount, setFrameCount] = useState(8);
  const [frameSize, setFrameSize] = useState(128);

  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  // Fetch available motions
  useEffect(() => {
    getMotions()
      .then(setMotions)
      .catch(() => setMotions(DEFAULT_MOTIONS));
  }, []);

  // Poll for task status
  useEffect(() => {
    if (!taskId || taskStatus?.status === 'completed' || taskStatus?.status === 'failed') {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const status = await getTaskStatus(taskId);
        setTaskStatus(status);

        if (status.status === 'completed' || status.status === 'failed') {
          setIsGenerating(false);
        }
      } catch (error) {
        console.error('Failed to get status:', error);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [taskId, taskStatus?.status]);

  const handleGenerate = useCallback(async () => {
    if (!selectedFile) return;

    setIsGenerating(true);
    setTaskStatus({ task_id: '', status: 'processing', progress: 10 });

    try {
      // API now runs synchronously and returns full result
      const result = await generateSprite(
        selectedFile,
        selectedMotion,
        frameCount,
        frameSize
      );
      setTaskId(result.task_id);
      setTaskStatus(result);
      setIsGenerating(false);
    } catch (error) {
      console.error('Failed to generate:', error);
      setTaskStatus({ task_id: '', status: 'failed', error: 'Generation failed' });
      setIsGenerating(false);
    }
  }, [selectedFile, selectedMotion, frameCount, frameSize]);

  const handleDownload = useCallback(() => {
    if (!taskId) return;
    window.open(getDownloadUrl(taskId), '_blank');
  }, [taskId]);

  const handleReset = useCallback(() => {
    setSelectedFile(null);
    setTaskId(null);
    setTaskStatus(null);
    setIsGenerating(false);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">Spritify</h1>
          <p className="text-gray-600">
            Transform static images into animated sprite sheets
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8 space-y-8">
          {/* Step 1: Upload */}
          <section>
            <h2 className="text-lg font-semibold text-gray-700 mb-4">
              1. Upload your character
            </h2>
            <ImageUploader onFileSelected={setSelectedFile} />
          </section>

          {/* Step 2: Select Motion */}
          {selectedFile && (
            <section>
              <h2 className="text-lg font-semibold text-gray-700 mb-4">
                2. Choose a motion
              </h2>
              <MotionSelector
                motions={motions}
                selected={selectedMotion}
                onSelect={setSelectedMotion}
              />
            </section>
          )}

          {/* Step 3: Settings */}
          {selectedFile && (
            <section>
              <h2 className="text-lg font-semibold text-gray-700 mb-4">
                3. Settings
              </h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    Frame Count
                  </label>
                  <select
                    value={frameCount}
                    onChange={(e) => setFrameCount(Number(e.target.value))}
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {[4, 6, 8, 12, 16].map((n) => (
                      <option key={n} value={n}>
                        {n} frames
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    Frame Size
                  </label>
                  <select
                    value={frameSize}
                    onChange={(e) => setFrameSize(Number(e.target.value))}
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {[64, 128, 256, 512].map((n) => (
                      <option key={n} value={n}>
                        {n}x{n} px
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </section>
          )}

          {/* Generate Button */}
          {selectedFile && !taskStatus && (
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="w-full py-4 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isGenerating ? 'Starting...' : 'Generate Sprite Sheet'}
            </button>
          )}

          {/* Progress */}
          {taskStatus && taskStatus.status !== 'completed' && (
            <GenerationProgress
              status={taskStatus.status}
              progress={taskStatus.progress || 0}
              error={taskStatus.error}
            />
          )}

          {/* Result */}
          {taskStatus?.status === 'completed' && taskStatus.result_url && (
            <section className="space-y-6">
              <h2 className="text-lg font-semibold text-gray-700">
                Your Sprite Sheet
              </h2>

              <div className="flex flex-col lg:flex-row gap-8 items-start">
                {/* Preview */}
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-gray-600 mb-3">
                    Animation Preview
                  </h3>
                  <SpritePreview
                    spriteUrl={taskStatus.result_url}
                    frameCount={frameCount}
                    frameSize={frameSize}
                  />
                </div>

                {/* Full sprite sheet */}
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-gray-600 mb-3">
                    Full Sprite Sheet
                  </h3>
                  <img
                    src={taskStatus.result_url}
                    alt="Sprite Sheet"
                    className="border border-gray-200 rounded-lg max-w-full"
                    style={{ imageRendering: 'pixelated' }}
                  />
                </div>
              </div>

              <div className="flex gap-4">
                <button
                  onClick={handleDownload}
                  className="flex-1 py-3 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 transition"
                >
                  Download PNG
                </button>
                <button
                  onClick={handleReset}
                  className="flex-1 py-3 bg-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-300 transition"
                >
                  Create Another
                </button>
              </div>
            </section>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-gray-400 text-sm mt-8">
          Powered by AnimatedDrawings
        </p>
      </div>
    </div>
  );
}

export default App;
