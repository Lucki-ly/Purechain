import axios from 'axios';

// 与后端 FastAPI 对齐：默认本地 8000 端口，统一使用 /api 前缀
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 120000,
});

export const uploadFiles = async (files) => {
  const formData = new FormData();
  Array.from(files).forEach((file) => formData.append('files', file));

  const res = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const analyzeData = async (query, dfData) => {
  const res = await api.post('/analyze', {
    query,
    df_data: dfData,
  });
  return res.data;
};

export const chatWithAgent = async ({ query, messages, dfData, signal }) => {
  const res = await api.post('/chat', {
    query,
    messages,
    df_data: dfData ?? null,
  }, { signal });
  return res.data;
};

export default api;