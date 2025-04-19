<template>
  <div class="results-page">
    <h1>文档生成结果</h1>
    
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>
    
    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="fetchDocument" class="btn">重试</button>
      <router-link to="/" class="btn">返回首页</router-link>
    </div>
    
    <div v-else class="document-result">
      <!-- 处理中状态 -->
      <div v-if="document.status === 'processing' || document.status === 'queued'" class="processing">
        <h2>{{ document.topic }}</h2>
        <p class="status">状态: {{ getStatusText(document.status) }}</p>
        
        <!-- 进度条 -->
        <div class="progress-container">
          <div class="progress-bar" :style="{ width: `${progress * 100}%` }"></div>
        </div>
        <p class="progress-text">{{ Math.round(progress * 100) }}% - {{ progressMessage }}</p>
        
        <!-- 添加动画效果 -->
        <div class="processing-animation">
          <div class="dot"></div>
          <div class="dot"></div>
          <div class="dot"></div>
        </div>
        
        <p class="info">请耐心等待，文档生成可能需要几分钟时间...</p>
      </div>
      
      <!-- 失败状态 -->
      <div v-else-if="document.status === 'failed'" class="failed">
        <h2>{{ document.topic }}</h2>
        <p class="status error">生成失败</p>
        <p>{{ progressMessage || '文档生成过程中出现错误' }}</p>
        <router-link to="/generate" class="btn">重新尝试</router-link>
      </div>
      
      <!-- 完成状态 -->
      <div v-else-if="document.status === 'completed'" class="completed">
        <h2>{{ document.topic }}</h2>
        <p class="status success">生成完成</p>
        
        <div class="document-actions">
          <a :href="getCorrectUrl(document.download_url)" class="btn download" download>下载文档</a>
          <a :href="getCorrectUrl(document.preview_url)" class="btn preview" target="_blank">预览文档</a>
        </div>
        
        <router-link to="/generate" class="btn secondary">创建新文档</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex';

export default {
  name: 'Results',
  data() {
    return {
      document: null,
      loading: true,
      error: null,
      progress: 0,
      progressMessage: '',
      statusCheckInterval: null,
      eventSource: null
    };
  },
  created() {
    // 首先尝试从 localStorage 获取
    const savedDoc = localStorage.getItem('currentDocument');
    if (savedDoc) {
      this.document = JSON.parse(savedDoc);
      this.loading = false;
      
      if (this.document.status === 'processing' || this.document.status === 'queued') {
        // 使用 SSE 替代轮询
        this.startEventStream(this.document.id);
      }
    } else {
      // 如果 localStorage 中没有数据，再尝试从 API 获取
      this.fetchDocument();
    }
  },
  beforeDestroy() {
    // 清除 EventSource
    if (this.eventSource) {
      this.eventSource.close();
    }
    
    // 清除定时器
    if (this.statusCheckInterval) {
      clearInterval(this.statusCheckInterval);
    }
  },
  methods: {
    ...mapActions('documents', ['getDocument', 'getDocumentStatus']),
    
    async fetchDocument() {
      this.loading = true;
      this.error = null;
      
      try {
        const documentId = this.$route.params.id;
        const response = await this.getDocument(documentId);
        this.document = response;
        
        // 如果文档正在处理中，开始 SSE 流
        if (this.document.status === 'processing' || this.document.status === 'queued') {
          this.startEventStream(documentId);
        }
        
        this.loading = false;
      } catch (error) {
        this.loading = false;
        this.error = '获取文档信息失败';
        console.error(error);
        
        // 尝试从 localStorage 获取
        const savedDoc = localStorage.getItem('currentDocument');
        if (savedDoc) {
          this.document = JSON.parse(savedDoc);
          this.loading = false;
          this.error = null;
          
          if (this.document.status === 'processing' || this.document.status === 'queued') {
            this.startEventStream(this.document.id);
          }
        }
      }
    },
    
    startEventStream(documentId) {
      // 关闭现有的 EventSource
      if (this.eventSource) {
        this.eventSource.close();
      }
      
      // 创建新的 EventSource
      const apiUrl = process.env.VUE_APP_API_URL || 'http://localhost:8001/api/v1';
      this.eventSource = new EventSource(`${apiUrl}/documents/${documentId}/stream`);
      
      // 监听消息
      this.eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('SSE update:', data);
        
        // 更新进度和消息
        if (data.progress !== undefined) {
          this.progress = data.progress;
        }
        
        if (data.message) {
          this.progressMessage = data.message;
        }
        
        // 更新主题（如果存在）
        if (data.topic && (!this.document.topic || this.document.topic === '未知')) {
          this.document.topic = data.topic;
        }
        
        // 更新文档状态
        if (data.status && data.status !== this.document.status) {
          this.document.status = data.status;
          
          // 如果完成或失败，更新文档信息并关闭流
          if (data.status === 'completed' || data.status === 'failed') {
            if (data.download_url) {
              this.document.download_url = data.download_url;
            }
            
            if (data.preview_url) {
              this.document.preview_url = data.preview_url;
            }
            
            // 更新localStorage
            localStorage.setItem('currentDocument', JSON.stringify(this.document));
            
            this.eventSource.close();
          }
        }
      };
      
      // 错误处理
      this.eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
        this.eventSource.close();
        
        // 如果 SSE 失败，回退到轮询
        this.startStatusPolling(documentId);
      };
    },
    
    startStatusPolling(documentId) {
      // 每2秒检查一次状态
      this.statusCheckInterval = setInterval(async () => {
        try {
          const statusResponse = await this.getDocumentStatus(documentId);
          this.progress = statusResponse.progress;
          this.progressMessage = statusResponse.message;
          
          // 如果状态已经变化，重新获取文档信息
          if (statusResponse.status !== this.document.status) {
            await this.fetchDocument();
          }
          
          // 如果已完成或失败，停止轮询
          if (statusResponse.status === 'completed' || statusResponse.status === 'failed') {
            clearInterval(this.statusCheckInterval);
          }
        } catch (error) {
          console.error('获取状态失败', error);
          
          // 检查是否应该停止轮询
          if (error.stopPolling || (error.response && error.response.status === 404)) {
            clearInterval(this.statusCheckInterval);
            this.progressMessage = '无法继续跟踪文档状态，可能文档已被删除或不存在。';
            
            // 如果有错误细节，显示出来
            if (error.response && error.response.data && error.response.data.detail) {
              this.progressMessage += ' ' + error.response.data.detail;
            }
            
            // 更新文档状态为失败
            this.document.status = 'failed';
            localStorage.setItem('currentDocument', JSON.stringify(this.document));
            
            console.warn('已停止轮询文档状态', documentId);
          }
        }
      }, 2000);
    },
    
    getStatusText(status) {
      const statusMap = {
        'queued': '排队中',
        'processing': '处理中',
        'completed': '已完成',
        'failed': '失败'
      };
      return statusMap[status] || status;
    },
    
    getCorrectUrl(url) {
      if (!url) return '#';
      
      // 检查URL是否是以http开头的完整URL
      if (url.startsWith('http')) {
        return url;
      }
      
      // 如果是相对路径，则添加API基础URL
      const baseUrl = process.env.VUE_APP_API_URL || 'http://localhost:8001';
      if (url.startsWith('/')) {
        return `${baseUrl}${url}`;
      }
      
      // 其他情况，直接添加到baseUrl
      return `${baseUrl}/${url}`;
    }
  }
};
</script>

<style scoped>
.results-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  text-align: center;
  margin-bottom: 30px;
}

.loading, .error {
  text-align: center;
  margin: 40px 0;
}

.document-result {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.status {
  font-weight: bold;
  margin: 15px 0;
}

.error {
  color: #f44336;
}

.success {
  color: #4CAF50;
}

.progress-container {
  width: 100%;
  height: 20px;
  background-color: #e0e0e0;
  border-radius: 10px;
  margin: 20px 0;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background-color: #4CAF50;
  transition: width 0.5s ease;
}

.progress-text {
  text-align: center;
  margin-bottom: 20px;
}

.info {
  color: #666;
  font-style: italic;
  text-align: center;
}

.document-actions {
  display: flex;
  gap: 15px;
  margin: 25px 0;
}

.btn {
  display: inline-block;
  padding: 10px 20px;
  border-radius: 4px;
  text-decoration: none;
  font-weight: bold;
  text-align: center;
  cursor: pointer;
  border: none;
  margin: 5px;
}

.download {
  background-color: #4CAF50;
  color: white;
}

.preview {
  background-color: #2196F3;
  color: white;
}

.secondary {
  background-color: #9e9e9e;
  color: white;
}

.processing-animation {
  display: flex;
  justify-content: center;
  margin: 20px 0;
}

.dot {
  width: 12px;
  height: 12px;
  background-color: #4CAF50;
  border-radius: 50%;
  margin: 0 5px;
  animation: pulse 1.5s infinite ease-in-out;
}

.dot:nth-child(2) {
  animation-delay: 0.5s;
}

.dot:nth-child(3) {
  animation-delay: 1s;
}

@keyframes pulse {
  0%, 100% { transform: scale(0.8); opacity: 0.5; }
  50% { transform: scale(1.2); opacity: 1; }
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border-left-color: #4CAF50;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style> 