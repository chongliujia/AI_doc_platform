<template>
  <div class="outline-preview-page">
    <div class="container">
      <h1 class="page-title">文档大纲预览</h1>
      
      <div class="workflow-steps">
        <div class="workflow-step completed">
          <div class="step-number">1</div>
          <div class="step-content">
            <h3>编辑基本信息</h3>
            <p>已完成</p>
          </div>
        </div>
        <div class="workflow-connector completed"></div>
        <div class="workflow-step active">
          <div class="step-number">2</div>
          <div class="step-content">
            <h3>预览并编辑大纲</h3>
            <p>当前步骤</p>
          </div>
        </div>
        <div class="workflow-connector"></div>
        <div class="workflow-step">
          <div class="step-number">3</div>
          <div class="step-content">
            <h3>生成完整文档</h3>
            <p>确认大纲后进行</p>
          </div>
        </div>
      </div>
      
      <div v-if="loading" class="loading-state">
        <div class="spinner-container">
          <div class="spinner"></div>
        </div>
        <p class="loading-message">正在生成大纲，请稍候...</p>
      </div>
      
      <div v-else-if="error" class="error-state">
        <div class="error-icon">
          <i class="fa fa-exclamation-triangle"></i>
        </div>
        <p class="error-message">{{ error }}</p>
        <button @click="goBack" class="btn btn-secondary">
          <i class="fa fa-arrow-left"></i> 返回修改基本信息
        </button>
      </div>
      
      <div v-else-if="outlineId" class="outline-editor-container">
        <outline-editor
          :outline-id="outlineId"
          :initial-items="outlineItems"
          :initial-topic="topic"
          :max-pages="maxPages"
          title="编辑文档大纲"
          @outline-saved="handleOutlineSaved"
          @outline-confirmed="handleOutlineConfirmed"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex';
import OutlineEditor from '@/components/OutlineEditor.vue';
import api from '@/services/api';

export default {
  name: 'OutlinePreview',
  components: {
    OutlineEditor
  },
  data() {
    return {
      loading: false,
      error: null,
      outlineId: null,
      outlineItems: [],
      topic: '',
      docType: '',
      additionalInfo: '',
      aiServiceType: 'deepseek',
      maxPages: null
    };
  },
  created() {
    // 从URL参数中获取数据
    this.topic = this.$route.query.topic || '';
    this.docType = this.$route.query.docType || 'ppt';
    this.additionalInfo = this.$route.query.additionalInfo || '';
    this.aiServiceType = this.$route.query.aiServiceType || 'deepseek';
    this.maxPages = this.$route.query.maxPages ? parseInt(this.$route.query.maxPages) : null;
    
    // 创建大纲预览
    this.createOutlinePreview();
  },
  methods: {
    async createOutlinePreview() {
      this.loading = true;
      this.error = null;
      
      try {
        const requestData = {
          topic: this.topic,
          doc_type: this.docType,
          additional_info: this.additionalInfo,
          ai_service_type: this.aiServiceType,
          max_pages: this.maxPages
        };
        
        const response = await api.createOutlinePreview(requestData);
        
        this.outlineId = response.data.id;
        this.outlineItems = response.data.outline_items;
        this.topic = response.data.topic;
      } catch (error) {
        console.error('创建大纲预览失败:', error);
        this.error = '创建大纲预览失败: ' + (error.response && error.response.data && error.response.data.detail || error.message);
      } finally {
        this.loading = false;
      }
    },
    
    handleOutlineSaved(data) {
      console.log('大纲已保存:', data);
    },
    
    async handleOutlineConfirmed(documentData) {
      console.log('大纲已确认，文档创建成功:', documentData);
      
      // 存储文档信息并跳转到结果页面
      localStorage.setItem('currentDocument', JSON.stringify(documentData));
      this.$router.push(`/results/${documentData.id}`);
    },
    
    goBack() {
      this.$router.push('/generate');
    }
  }
};
</script>

<style scoped>
.outline-preview-page {
  background-color: #f5f7fa;
  min-height: 100vh;
  padding: 40px 0;
}

.container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 20px;
}

.page-title {
  text-align: center;
  margin-bottom: 40px;
  color: #2c3e50;
  font-size: 32px;
  font-weight: 600;
}

.workflow-steps {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 40px 0;
  position: relative;
}

.workflow-step {
  flex: 1;
  display: flex;
  background-color: #ffffff;
  border-radius: 10px;
  padding: 20px;
  align-items: center;
  box-shadow: 0 3px 8px rgba(0,0,0,0.08);
  position: relative;
  z-index: 1;
  max-width: 280px;
  min-width: 240px;
  transition: all 0.3s ease;
}

.workflow-connector {
  height: 3px;
  background-color: #e0e0e0;
  flex-grow: 0.5;
  max-width: 80px;
  position: relative;
  z-index: 0;
}

.workflow-connector.completed {
  background-color: #4caf50;
}

.workflow-step.active {
  background-color: #e3f2fd;
  border: 2px solid #2196f3;
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(33, 150, 243, 0.15);
}

.workflow-step.completed {
  background-color: #e8f5e9;
  border: 1px solid #4caf50;
}

.workflow-step .step-number {
  background-color: #9e9e9e;
  color: white;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-right: 20px;
  font-size: 18px;
  flex-shrink: 0;
}

.workflow-step.active .step-number {
  background-color: #2196f3;
  box-shadow: 0 3px 6px rgba(33, 150, 243, 0.3);
}

.workflow-step.completed .step-number {
  background-color: #4caf50;
}

.workflow-step .step-content {
  flex-grow: 1;
}

.workflow-step .step-content h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #424242;
}

.workflow-step.active .step-content h3 {
  color: #1976d2;
  font-weight: 600;
}

.workflow-step .step-content p {
  margin: 0;
  font-size: 14px;
  color: #757575;
}

.loading-state, .error-state {
  text-align: center;
  padding: 60px 0;
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  margin-top: 40px;
}

.spinner-container {
  margin-bottom: 30px;
}

.spinner {
  width: 60px;
  height: 60px;
  border: 5px solid rgba(33, 150, 243, 0.1);
  border-top: 5px solid #2196f3;
  border-radius: 50%;
  margin: 0 auto;
  animation: spin 1s linear infinite;
}

.loading-message {
  font-size: 18px;
  color: #616161;
  margin: 0;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon {
  color: #f44336;
  font-size: 48px;
  margin-bottom: 20px;
}

.error-message {
  color: #d32f2f;
  margin-bottom: 30px;
  font-size: 18px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.btn {
  font-weight: 600;
  border-radius: 6px;
  padding: 12px 24px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-secondary {
  background-color: #78909c;
  color: white;
}

.btn-secondary:hover {
  background-color: #607d8b;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.outline-editor-container {
  margin-top: 40px;
}

@media (max-width: 900px) {
  .workflow-steps {
    flex-direction: column;
    gap: 30px;
  }
  
  .workflow-step {
    width: 100%;
    max-width: 100%;
  }
  
  .workflow-connector {
    width: 3px;
    height: 30px;
    max-width: 3px;
  }
  
  .page-title {
    font-size: 28px;
  }
}
</style> 