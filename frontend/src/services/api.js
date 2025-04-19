import axios from 'axios';

// 根据当前URL选择合适的API路径
const currentPort = window.location.port;
const API_URL = currentPort === '3000' 
  ? 'http://localhost:8001/api/v1'  // 前端在3000端口时直接访问后端
  : '/api/v1';                      // 其他情况使用相对路径

console.log('使用API URL:', API_URL, '当前端口:', currentPort);

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 180000, // 180秒超时，大幅增加超时时间以避免大型文档生成失败
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// 添加响应拦截器，用于调试
apiClient.interceptors.response.use(
  response => {
    console.log('API 响应成功:', response);
    return response;
  },
  error => {
    console.error('API Error:', error.response || error.message);
    return Promise.reject(error);
  }
);

// 添加请求拦截器，用于调试
apiClient.interceptors.request.use(
  config => {
    console.log('API 请求:', config.method.toUpperCase(), config.url, config.data || {});
    return config;
  },
  error => {
    console.error('请求配置错误:', error);
    return Promise.reject(error);
  }
);

export default {
  // 大纲预览相关API
  createOutlinePreview(data) {
    return apiClient.post('/outline-preview/', data);
  },
  
  updateOutlinePreview(previewId, data) {
    return apiClient.put(`/outline-preview/${previewId}`, data);
  },
  
  confirmOutline(data) {
    return apiClient.post('/outline-confirm/', data);
  },

  // 文档生成相关API
  createDocument(data) {
    return apiClient.post('/documents/', data);
  },
  
  createAdvancedDocument(data) {
    return apiClient.post('/advanced-documents/', data);
  },
  
  getDocumentStatus(id) {
    return apiClient.get(`/documents/${id}/status`);
  },
  
  getDocument(id) {
    return apiClient.get(`/documents/${id}`);
  },
  
  // 获取文档列表
  getDocuments() {
    return apiClient.get('/documents/');
  }
}; 