<template>
  <div class="document-form">
    <h2>创建新文档</h2>
    
    <form @submit.prevent="submitForm">
      <div class="form-group">
        <label for="topic">文档主题</label>
        <input 
          id="topic" 
          v-model="topic" 
          type="text" 
          required 
          placeholder="输入文档主题"
        />
      </div>
      
      <div class="form-group">
        <label for="docType">文档类型</label>
        <select id="docType" v-model="docType" required>
          <option value="ppt">PPT演示文稿</option>
          <option value="word">Word文档</option>
          <option value="pdf">PDF文档</option>
        </select>
      </div>
      
      <div class="form-group">
        <label for="maxPages">页数限制 (可选)</label>
        <input 
          id="maxPages" 
          v-model.number="maxPages" 
          type="number" 
          min="1" 
          max="100" 
          placeholder="输入最大页数，留空表示不限制"
        />
        <small class="field-hint">
          {{ getMaxPagesHint }}
        </small>
      </div>
      
      <div class="form-group">
        <label for="additionalInfo">额外信息 (可选)</label>
        <textarea 
          id="additionalInfo" 
          v-model="additionalInfo" 
          placeholder="输入任何额外的要求或信息"
          rows="4"
        ></textarea>
      </div>
      
      <div class="form-group">
        <label for="aiServiceType">AI服务类型 (可选)</label>
        <select id="aiServiceType" v-model="aiServiceType">
          <option value="deepseek">DeepSeek</option>
          <option value="openai">OpenAI</option>
        </select>
      </div>
      
      <div class="form-group">
        <label for="template">选择模板 (可选)</label>
        <select id="template" v-model="templateId">
          <option value="default">默认模板</option>
          <option v-for="template in templates" :key="template.id" :value="template.id">
            {{ template.name }}
          </option>
        </select>
      </div>
      
      <div class="form-actions">
        <button type="button" @click="previewOutline" class="btn preview-btn primary">
          <i class="fa fa-list-ul"></i> 预览大纲并继续
        </button>
      </div>
      
      <div class="advanced-link">
        需要更精确控制? <a href="#" @click.prevent="$emit('switch-mode')">切换到高级模式</a>
      </div>
    </form>
  </div>
</template>

<script>
import { mapActions } from 'vuex';

export default {
  name: 'DocumentForm',
  data() {
    return {
      topic: '',
      docType: 'ppt',
      maxPages: null,
      additionalInfo: '',
      aiServiceType: 'deepseek',
      templateId: 'default',
      submitting: false,
      error: null,
      templates: [
        { id: 'business', name: '商务模板' },
        { id: 'academic', name: '学术模板' },
        { id: 'creative', name: '创意模板' }
      ]
    };
  },
  computed: {
    getMaxPagesHint() {
      if (!this.docType) return '';
      
      switch(this.docType) {
        case 'ppt':
          return '推荐范围：10-30页幻灯片';
        case 'word':
          return '推荐范围：5-20页文档';
        case 'pdf':
          return '推荐范围：5-20页文档';
        default:
          return '';
      }
    }
  },
  methods: {
    ...mapActions('documents', ['createDocument']),
    
    async submitForm() {
      if (!this.topic) {
        this.error = '请输入文档主题';
        return;
      }
      
      this.submitting = true;
      this.error = null;
      
      try {
        const documentData = {
          topic: this.topic,
          doc_type: this.docType,
          additional_info: this.additionalInfo,
          ai_service_type: this.aiServiceType,
          template_id: this.templateId,
          max_pages: this.maxPages
        };
        
        const response = await this.createDocument(documentData);
        console.log('Document created, full response:', response);
        
        // 确保存储完整的响应对象
        localStorage.setItem('currentDocument', JSON.stringify(response));
        
        // 确保使用正确的 ID
        this.$router.push(`/results/${response.id}`);
      } catch (error) {
        this.error = '创建文档时出错，请重试';
        console.error('Submit error:', error);
      } finally {
        this.submitting = false;
      }
    },
    
    async previewOutline() {
      if (!this.topic) {
        this.error = '请输入文档主题';
        return;
      }
      
      this.submitting = true;
      this.error = null;
      
      try {
        // 导航到大纲预览页面，并传递表单数据
        this.$router.push({
          path: '/outline-preview',
          query: {
            topic: this.topic,
            docType: this.docType,
            additionalInfo: this.additionalInfo,
            aiServiceType: this.aiServiceType,
            maxPages: this.maxPages
          }
        });
      } catch (error) {
        this.error = '创建大纲预览时出错，请重试';
        console.error('Preview error:', error);
      } finally {
        this.submitting = false;
      }
    }
  }
};
</script>

<style scoped>
.document-form {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

input, select, textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.field-hint {
  display: block;
  margin-top: 5px;
  color: #666;
  font-size: 0.8rem;
}

button {
  background-color: #4CAF50;
  color: white;
  padding: 12px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.submit-btn {
  background-color: #757575;
  color: white;
  flex: 1;
}

.preview-btn {
  background-color: #4CAF50;
  color: white;
  flex: 1.5;
  font-weight: bold;
}

.advanced-link {
  margin-top: 20px;
  text-align: center;
  font-size: 14px;
  color: #666;
}

.advanced-link a {
  color: #4CAF50;
  text-decoration: none;
}

.advanced-link a:hover {
  text-decoration: underline;
}
</style> 