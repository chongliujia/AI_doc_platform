<template>
  <div class="advanced-document-form">
    <h2>高级文档创建</h2>
    
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
        <select id="docType" v-model="docType" required @change="updatePlaceholders">
          <option value="ppt">PPT演示文稿</option>
          <option value="word">Word文档</option>
          <option value="pdf">PDF文档</option>
        </select>
      </div>
      
      <div class="form-group">
        <label for="maxPages">最大页数限制 (可选)</label>
        <input 
          id="maxPages" 
          v-model.number="maxPages" 
          type="number" 
          min="1"
          :placeholder="`限制最大${docType === 'ppt' ? '页数' : '章节数'}`"
        />
      </div>
      
      <div class="form-group">
        <label for="additionalInfo">额外信息 (可选)</label>
        <textarea 
          id="additionalInfo" 
          v-model="additionalInfo" 
          placeholder="输入任何额外的要求或信息"
          rows="3"
        ></textarea>
      </div>
      
      <div class="form-group">
        <label for="aiServiceType">AI服务类型 (可选)</label>
        <select id="aiServiceType" v-model="aiServiceType">
          <option value="deepseek">DeepSeek</option>
          <option value="openai">OpenAI</option>
        </select>
      </div>
      
      <!-- 自定义内容部分 -->
      <div class="custom-content-section">
        <h3>自定义内容 <button type="button" class="add-btn" @click="addContentItem">+ 添加</button></h3>
        
        <div v-if="detailedContent.length === 0" class="empty-state">
          点击"添加"按钮来定义具体的{{ docType === 'ppt' ? '页面' : '章节' }}内容
        </div>
        
        <div v-for="(item, index) in detailedContent" :key="index" class="content-item">
          <div class="content-header">
            <span class="item-number">{{ index + 1 }}</span>
            <button type="button" class="remove-btn" @click="removeContentItem(index)">删除</button>
          </div>
          
          <div class="form-group">
            <label :for="`title-${index}`">{{ docType === 'ppt' ? '页面' : '章节' }}标题</label>
            <input 
              :id="`title-${index}`" 
              v-model="item.title" 
              type="text" 
              required 
              :placeholder="`输入${docType === 'ppt' ? '页面' : '章节'}标题`"
            />
          </div>
          
          <div class="form-group">
            <label :for="`content-${index}`">内容 (可选)</label>
            <textarea 
              :id="`content-${index}`" 
              v-model="item.content" 
              :placeholder="`输入${docType === 'ppt' ? '页面' : '章节'}内容，不填写将由AI生成`"
              rows="3"
            ></textarea>
          </div>
        </div>
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
        <button type="button" class="btn secondary" @click="$emit('switch-mode')">
          切换到基础模式
        </button>
        <button type="button" class="btn preview" @click="previewOutline" :disabled="submitting">
          <i class="fa fa-list-ul"></i> 预览大纲并继续
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { mapActions } from 'vuex';

export default {
  name: 'AdvancedDocumentForm',
  data() {
    return {
      topic: '',
      docType: 'ppt',
      maxPages: null,
      additionalInfo: '',
      templateId: 'default',
      detailedContent: [],
      submitting: false,
      error: null,
      templates: [
        { id: 'business', name: '商务模板' },
        { id: 'academic', name: '学术模板' },
        { id: 'creative', name: '创意模板' }
      ],
      aiServiceType: 'deepseek'
    };
  },
  methods: {
    ...mapActions('documents', ['createAdvancedDocument']),
    
    addContentItem() {
      this.detailedContent.push({
        title: '',
        content: '',
        position: this.detailedContent.length + 1
      });
    },
    
    removeContentItem(index) {
      this.detailedContent.splice(index, 1);
      
      // 更新剩余项的位置
      this.detailedContent.forEach((item, idx) => {
        item.position = idx + 1;
      });
    },
    
    updatePlaceholders() {
      // 当文档类型变更时，可以添加一些逻辑来调整UI
      console.log(`文档类型更改为: ${this.docType}`);
    },
    
    async submitForm() {
      if (!this.topic) {
        this.error = '请输入文档主题';
        return;
      }
      
      this.submitting = true;
      this.error = null;
      
      try {
        // 准备表单数据
        const documentData = {
          topic: this.topic,
          doc_type: this.docType,
          additional_info: this.additionalInfo,
          template_id: this.templateId,
          max_pages: this.maxPages,
          detailed_content: this.detailedContent.length > 0 ? this.detailedContent : null,
          is_advanced_mode: true,
          ai_service_type: this.aiServiceType
        };
        
        // 调用Vuex action
        const response = await this.createAdvancedDocument(documentData);
        console.log('Advanced document created, response:', response);
        
        // 存储文档信息并跳转
        localStorage.setItem('currentDocument', JSON.stringify(response));
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
            aiServiceType: this.aiServiceType
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
.advanced-document-form {
  max-width: 800px;
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

.custom-content-section {
  margin: 30px 0;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.custom-content-section h3 {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.add-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 5px 10px;
  cursor: pointer;
  font-size: 14px;
}

.content-item {
  background-color: white;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 15px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.item-number {
  display: inline-block;
  width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  background-color: #4CAF50;
  color: white;
  border-radius: 50%;
  font-weight: bold;
}

.remove-btn {
  background-color: #ff5252;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 3px 8px;
  cursor: pointer;
  font-size: 12px;
}

.empty-state {
  padding: 20px;
  text-align: center;
  background-color: white;
  border-radius: 4px;
  color: #888;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-top: 20px;
}

.btn {
  padding: 10px 15px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  flex: 1;
}

.primary {
  background-color: #4CAF50;
  color: white;
}

.secondary {
  background-color: #757575;
  color: white;
}

.preview {
  background-color: #4CAF50;
  color: white;
  flex: 1.5;
  font-weight: bold;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}
</style> 