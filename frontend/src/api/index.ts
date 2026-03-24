import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
});

export interface Motion {
  id: string;
  name: string;
  description: string;
}

export interface GenerationResponse {
  task_id: string;
  status: string;
}

export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result_url?: string;
  error?: string;
}

export const getMotions = async (): Promise<Motion[]> => {
  const response = await api.get('/motions');
  return response.data.motions;
};

export const generateSprite = async (
  image: File,
  motionId: string,
  frameCount: number = 8,
  frameSize: number = 128
): Promise<TaskStatus> => {
  const formData = new FormData();
  formData.append('image', image);
  formData.append('motion_id', motionId);
  formData.append('frame_count', frameCount.toString());
  formData.append('frame_size', frameSize.toString());

  // This now returns the full TaskStatus since the API runs synchronously
  const response = await api.post('/generate', formData, {
    timeout: 120000, // 2 minute timeout for generation
  });
  return response.data;
};

export const getTaskStatus = async (taskId: string): Promise<TaskStatus> => {
  const response = await api.get(`/status/${taskId}`);
  return response.data;
};

export const getDownloadUrl = (taskId: string): string => {
  return `/api/v1/download/${taskId}`;
};
