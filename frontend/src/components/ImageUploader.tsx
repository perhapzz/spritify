import { useRef } from 'react';
import { useFileUpload } from '../hooks/useFileUpload';

interface ImageUploaderProps {
  onFileSelected: (file: File) => void;
}

export function ImageUploader({ onFileSelected }: ImageUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const { preview, error, handleFileSelect, handleDrop, clearFile } =
    useFileUpload();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(e);
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      onFileSelected(selectedFile);
    }
  };

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    handleDrop(e);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      onFileSelected(droppedFile);
    }
  };

  return (
    <div className="w-full">
      <div
        onClick={() => inputRef.current?.click()}
        onDrop={onDrop}
        onDragOver={(e) => e.preventDefault()}
        className={`
          relative border-2 border-dashed rounded-xl p-8
          flex flex-col items-center justify-center
          cursor-pointer transition-all duration-200
          ${
            preview
              ? 'border-green-400 bg-green-50'
              : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
          }
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          onChange={handleChange}
          className="hidden"
        />

        {preview ? (
          <div className="relative">
            <img
              src={preview}
              alt="Preview"
              className="max-h-64 rounded-lg shadow-md"
            />
            <button
              onClick={(e) => {
                e.stopPropagation();
                clearFile();
              }}
              className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm hover:bg-red-600"
            >
              ×
            </button>
          </div>
        ) : (
          <>
            <svg
              className="w-12 h-12 text-gray-400 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <p className="text-gray-600 text-center">
              <span className="font-medium text-blue-500">Click to upload</span>{' '}
              or drag and drop
            </p>
            <p className="text-gray-400 text-sm mt-1">PNG, JPG, WebP up to 10MB</p>
          </>
        )}
      </div>

      {error && (
        <p className="text-red-500 text-sm mt-2 text-center">{error}</p>
      )}
    </div>
  );
}
