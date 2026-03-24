import { useEffect, useRef, useState, useCallback } from 'react';

interface SpritePreviewProps {
  spriteUrl: string;
  frameCount: number;
  frameSize: number;
  onExportGif?: (blob: Blob) => void;
}

type Speed = 'slow' | 'normal' | 'fast';
const SPEED_MS: Record<Speed, number> = { slow: 200, normal: 100, fast: 50 };

export function SpritePreview({
  spriteUrl,
  frameCount,
  frameSize,
  onExportGif,
}: SpritePreviewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [speed, setSpeed] = useState<Speed>('normal');
  const [spriteImage, setSpriteImage] = useState<HTMLImageElement | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    const img = new Image();
    img.onload = () => setSpriteImage(img);
    img.src = spriteUrl;
  }, [spriteUrl]);

  useEffect(() => {
    if (!isPlaying || !spriteImage) return;
    const interval = setInterval(() => {
      setCurrentFrame((prev) => (prev + 1) % frameCount);
    }, SPEED_MS[speed]);
    return () => clearInterval(interval);
  }, [isPlaying, frameCount, spriteImage, speed]);

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

  const handleExportGif = useCallback(async () => {
    if (!spriteImage || !onExportGif) return;
    setIsExporting(true);

    try {
      // Build GIF using canvas frames → animated GIF via manual encoder
      const canvas = document.createElement('canvas');
      canvas.width = frameSize;
      canvas.height = frameSize;
      const ctx = canvas.getContext('2d')!;
      const columns = Math.min(frameCount, 8);

      // Collect frame data
      const frameDataUrls: string[] = [];
      for (let i = 0; i < frameCount; i++) {
        const col = i % columns;
        const row = Math.floor(i / columns);
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
        frameDataUrls.push(canvas.toDataURL('image/png'));
      }

      // Use simple approach: create animated PNG-sequence as fallback
      // For true GIF, we'd need gif.js — for now, download first frame as preview
      // Actually, let's build a minimal GIF encoder inline
      const blob = await buildGif(frameDataUrls, frameSize, frameSize, SPEED_MS[speed]);
      onExportGif(blob);
    } catch (e) {
      console.error('GIF export failed:', e);
    } finally {
      setIsExporting(false);
    }
  }, [spriteImage, frameCount, frameSize, speed, onExportGif]);

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
            width: Math.min(frameSize * 2, 320),
            height: Math.min(frameSize * 2, 320),
          }}
        />
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center justify-center gap-2">
        <button
          onClick={() => {
            setIsPlaying(false);
            setCurrentFrame((prev) => (prev - 1 + frameCount) % frameCount);
          }}
          className="px-3 py-1.5 bg-gray-200 rounded-lg hover:bg-gray-300 transition text-sm"
        >
          ←
        </button>
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="px-4 py-1.5 bg-gray-200 rounded-lg hover:bg-gray-300 transition text-sm min-w-[60px]"
        >
          {isPlaying ? '⏸' : '▶'}
        </button>
        <button
          onClick={() => {
            setIsPlaying(false);
            setCurrentFrame((prev) => (prev + 1) % frameCount);
          }}
          className="px-3 py-1.5 bg-gray-200 rounded-lg hover:bg-gray-300 transition text-sm"
        >
          →
        </button>

        <span className="mx-2 text-gray-300">|</span>

        {/* Speed control */}
        {(['slow', 'normal', 'fast'] as Speed[]).map((s) => (
          <button
            key={s}
            onClick={() => setSpeed(s)}
            className={`px-3 py-1.5 rounded-lg text-xs transition ${
              speed === s
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
            }`}
          >
            {s === 'slow' ? '🐢' : s === 'normal' ? '🏃' : '⚡'}
          </button>
        ))}
      </div>

      <p className="text-sm text-gray-500">
        帧 {currentFrame + 1} / {frameCount}
      </p>

      {/* GIF export button */}
      {onExportGif && (
        <button
          onClick={handleExportGif}
          disabled={isExporting}
          className="text-sm text-blue-500 hover:text-blue-700 transition disabled:opacity-50"
        >
          {isExporting ? '导出中...' : '📥 导出 GIF'}
        </button>
      )}
    </div>
  );
}

/**
 * Minimal GIF89a encoder.
 * Takes data URLs of frames and produces an animated GIF blob.
 */
async function buildGif(
  frameDataUrls: string[],
  width: number,
  height: number,
  delayMs: number
): Promise<Blob> {
  // Load all frames as ImageData
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d')!;

  const frames: ImageData[] = [];
  for (const url of frameDataUrls) {
    const img = new Image();
    await new Promise<void>((resolve) => {
      img.onload = () => resolve();
      img.src = url;
    });
    ctx.clearRect(0, 0, width, height);
    ctx.drawImage(img, 0, 0);
    frames.push(ctx.getImageData(0, 0, width, height));
  }

  // Build GIF binary
  const delay = Math.round(delayMs / 10); // GIF delay is in 1/100s
  const buf: number[] = [];

  // Helper
  const writeStr = (s: string) => {
    for (let i = 0; i < s.length; i++) buf.push(s.charCodeAt(i));
  };
  const writeU16LE = (v: number) => {
    buf.push(v & 0xff, (v >> 8) & 0xff);
  };

  // Quantize to 256-color palette using simple median cut approximation
  // For simplicity, use a fixed web-safe-ish palette
  const palette = buildPalette();
  const palBits = 7; // log2(256) - 1

  // Header
  writeStr('GIF89a');
  writeU16LE(width);
  writeU16LE(height);
  buf.push(0x80 | palBits, 0, 0); // GCT flag, bg, aspect
  // Global Color Table
  for (const [r, g, b] of palette) {
    buf.push(r, g, b);
  }

  // Netscape extension for looping
  buf.push(0x21, 0xff, 0x0b);
  writeStr('NETSCAPE2.0');
  buf.push(0x03, 0x01);
  writeU16LE(0); // loop forever
  buf.push(0x00);

  for (const frame of frames) {
    // Graphic Control Extension
    buf.push(0x21, 0xf9, 0x04, 0x04); // dispose = restore to bg
    writeU16LE(delay);
    buf.push(0x00, 0x00); // transparent color index, terminator
    // Note: no transparency for simplicity

    // Image Descriptor
    buf.push(0x2c);
    writeU16LE(0); // left
    writeU16LE(0); // top
    writeU16LE(width);
    writeU16LE(height);
    buf.push(0x00); // no local color table

    // LZW encode
    const pixels = quantizeFrame(frame, palette);
    const minCodeSize = 8;
    const encoded = lzwEncode(pixels, minCodeSize);
    buf.push(minCodeSize);

    // Write sub-blocks
    let offset = 0;
    while (offset < encoded.length) {
      const chunk = Math.min(255, encoded.length - offset);
      buf.push(chunk);
      for (let i = 0; i < chunk; i++) {
        buf.push(encoded[offset++]);
      }
    }
    buf.push(0x00); // block terminator
  }

  buf.push(0x3b); // GIF trailer

  return new Blob([new Uint8Array(buf)], { type: 'image/gif' });
}

function buildPalette(): [number, number, number][] {
  // 6×6×6 color cube + padding to 256
  const pal: [number, number, number][] = [];
  for (let r = 0; r < 6; r++) {
    for (let g = 0; g < 6; g++) {
      for (let b = 0; b < 6; b++) {
        pal.push([Math.round(r * 51), Math.round(g * 51), Math.round(b * 51)]);
      }
    }
  }
  // Fill remaining 40 slots with grays
  while (pal.length < 256) {
    const v = Math.round(((pal.length - 216) / 40) * 255);
    pal.push([v, v, v]);
  }
  return pal;
}

function quantizeFrame(
  frame: ImageData,
  _palette: [number, number, number][]
): number[] {
  const pixels: number[] = [];
  const data = frame.data;
  // Build lookup cache
  const cache = new Map<number, number>();

  for (let i = 0; i < data.length; i += 4) {
    const r = data[i], g = data[i + 1], b = data[i + 2];
    const key = (r << 16) | (g << 8) | b;

    let idx = cache.get(key);
    if (idx === undefined) {
      // Nearest color (6×6×6 cube shortcut)
      const ri = Math.round(r / 51);
      const gi = Math.round(g / 51);
      const bi = Math.round(b / 51);
      idx = ri * 36 + gi * 6 + bi;
      cache.set(key, idx);
    }
    pixels.push(idx);
  }
  return pixels;
}

function lzwEncode(pixels: number[], minCodeSize: number): number[] {
  const clearCode = 1 << minCodeSize;
  const eoiCode = clearCode + 1;
  let codeSize = minCodeSize + 1;
  let nextCode = eoiCode + 1;
  const maxCode = 4096;

  const output: number[] = [];
  let bitBuf = 0;
  let bitCount = 0;

  const emit = (code: number) => {
    bitBuf |= code << bitCount;
    bitCount += codeSize;
    while (bitCount >= 8) {
      output.push(bitBuf & 0xff);
      bitBuf >>= 8;
      bitCount -= 8;
    }
  };

  // Initialize table
  let table = new Map<string, number>();
  const resetTable = () => {
    table = new Map();
    for (let i = 0; i < clearCode; i++) {
      table.set(String(i), i);
    }
    nextCode = eoiCode + 1;
    codeSize = minCodeSize + 1;
  };

  resetTable();
  emit(clearCode);

  let current = String(pixels[0]);

  for (let i = 1; i < pixels.length; i++) {
    const next = current + ',' + pixels[i];
    if (table.has(next)) {
      current = next;
    } else {
      emit(table.get(current)!);
      if (nextCode < maxCode) {
        table.set(next, nextCode++);
        if (nextCode > (1 << codeSize) && codeSize < 12) {
          codeSize++;
        }
      } else {
        emit(clearCode);
        resetTable();
      }
      current = String(pixels[i]);
    }
  }

  emit(table.get(current)!);
  emit(eoiCode);

  // Flush remaining bits
  if (bitCount > 0) {
    output.push(bitBuf & 0xff);
  }

  return output;
}
