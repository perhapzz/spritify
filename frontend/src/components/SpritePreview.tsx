import { useEffect, useRef, useState } from 'react';

interface SpritePreviewProps {
  spriteUrl: string;
  frameCount: number;
  frameSize: number;
}

export function SpritePreview({
  spriteUrl,
  frameCount,
  frameSize,
}: SpritePreviewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [spriteImage, setSpriteImage] = useState<HTMLImageElement | null>(null);

  // Load sprite sheet image
  useEffect(() => {
    const img = new Image();
    img.onload = () => setSpriteImage(img);
    img.src = spriteUrl;
  }, [spriteUrl]);

  // Animation loop
  useEffect(() => {
    if (!isPlaying || !spriteImage) return;

    const interval = setInterval(() => {
      setCurrentFrame((prev) => (prev + 1) % frameCount);
    }, 100);

    return () => clearInterval(interval);
  }, [isPlaying, frameCount, spriteImage]);

  // Draw current frame
  useEffect(() => {
    if (!spriteImage || !canvasRef.current) return;

    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    const columns = Math.min(frameCount, 8);
    const col = currentFrame % columns;
    const row = Math.floor(currentFrame / columns);

    ctx.clearRect(0, 0, frameSize, frameSize);
    ctx.drawImage(
      spriteImage,
      col * frameSize,
      row * frameSize,
      frameSize,
      frameSize,
      0,
      0,
      frameSize,
      frameSize
    );
  }, [currentFrame, spriteImage, frameSize, frameCount]);

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="bg-gray-100 rounded-lg p-4 inline-block">
        <canvas
          ref={canvasRef}
          width={frameSize}
          height={frameSize}
          className="border border-gray-300 rounded"
          style={{
            imageRendering: 'pixelated',
            width: frameSize * 2,
            height: frameSize * 2,
          }}
        />
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300 transition"
        >
          {isPlaying ? 'Pause' : 'Play'}
        </button>
        <button
          onClick={() => {
            setIsPlaying(false);
            setCurrentFrame((prev) => (prev - 1 + frameCount) % frameCount);
          }}
          className="px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300 transition"
        >
          ←
        </button>
        <button
          onClick={() => {
            setIsPlaying(false);
            setCurrentFrame((prev) => (prev + 1) % frameCount);
          }}
          className="px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300 transition"
        >
          →
        </button>
      </div>

      <p className="text-sm text-gray-500">
        Frame {currentFrame + 1} / {frameCount}
      </p>
    </div>
  );
}
