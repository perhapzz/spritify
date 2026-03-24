import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
});

export type Mode = 'ai' | 'classic';

export interface Motion {
  id: string;
  name: string;
  description: string;
  frame_count?: number;
}

export interface TurnaroundResult {
  turnaround_id: string;
  provider: string;
  views: {
    front: string;
    side: string;
    back: string;
  };
}

export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result_url?: string;
  turnaround?: Record<string, string>;
  error?: string;
}

export const getMotions = async (mode: Mode = 'ai'): Promise<Motion[]> => {
  const response = await api.get('/motions', { params: { mode } });
  return response.data.motions;
};

export const generateTurnaround = async (image: File): Promise<TurnaroundResult> => {
  const formData = new FormData();
  formData.append('image', image);
  const response = await api.post('/turnaround', formData, { timeout: 120000 });
  return response.data;
};

export const generateSprite = async (
  image: File,
  motionId: string,
  frameCount: number = 8,
  frameSize: number = 128,
  mode: Mode = 'ai'
): Promise<TaskStatus> => {
  const formData = new FormData();
  formData.append('image', image);
  formData.append('motion_id', motionId);
  formData.append('frame_count', frameCount.toString());
  formData.append('frame_size', frameSize.toString());
  formData.append('mode', mode);

  const response = await api.post('/generate', formData, { timeout: 120000 });
  return response.data;
};

export const getTaskStatus = async (taskId: string): Promise<TaskStatus> => {
  const response = await api.get(`/status/${taskId}`);
  return response.data;
};

export const getDownloadUrl = (taskId: string): string => {
  return `/api/v1/download/${taskId}`;
};
