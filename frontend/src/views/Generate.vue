<template>
  <div class="generate-page">
    <h1>创建新文档</h1>
    
    <div class="workflow-guide">
      <div class="workflow-step active">
        <div class="step-number">1</div>
        <div class="step-content">
          <h3>编辑基本信息</h3>
          <p>输入文档主题、类型和其他基本信息</p>
        </div>
      </div>
      <div class="workflow-step">
        <div class="step-number">2</div>
        <div class="step-content">
          <h3>预览并编辑大纲</h3>
          <p>查看AI生成的大纲并按需修改 (推荐)</p>
        </div>
      </div>
      <div class="workflow-step">
        <div class="step-number">3</div>
        <div class="step-content">
          <h3>生成完整文档</h3>
          <p>确认大纲后生成最终文档</p>
        </div>
      </div>
    </div>
    
    <div class="mode-toggle">
      <button 
        :class="['toggle-btn', { active: !advancedMode }]" 
        @click="advancedMode = false"
      >
        基础模式
      </button>
      <button 
        :class="['toggle-btn', { active: advancedMode }]" 
        @click="advancedMode = true"
      >
        高级模式
      </button>
    </div>
    
    <document-form v-if="!advancedMode" @switch-mode="advancedMode = true" />
    <advanced-document-form v-else @switch-mode="advancedMode = false" />
  </div>
</template>

<script>
import DocumentForm from '../components/DocumentForm.vue';
import AdvancedDocumentForm from '../components/AdvancedDocumentForm.vue';

export default {
  name: 'Generate',
  components: {
    DocumentForm,
    AdvancedDocumentForm
  },
  data() {
    return {
      advancedMode: false
    }
  }
}
</script>

<style scoped>
.generate-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  text-align: center;
  margin-bottom: 20px;
}

.workflow-guide {
  display: flex;
  justify-content: space-between;
  margin: 30px 0;
  gap: 15px;
}

.workflow-step {
  flex: 1;
  display: flex;
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 15px;
  align-items: flex-start;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.workflow-step.active {
  background-color: #e8f5e9;
  border: 2px solid #4CAF50;
}

.step-number {
  background-color: #757575;
  color: white;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-right: 15px;
  flex-shrink: 0;
}

.workflow-step.active .step-number {
  background-color: #4CAF50;
}

.step-content h3 {
  margin: 0 0 5px 0;
  font-size: 16px;
}

.step-content p {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.mode-toggle {
  display: flex;
  justify-content: center;
  margin-bottom: 30px;
  background-color: #f0f0f0;
  border-radius: 8px;
  padding: 4px;
  width: 300px;
  margin-left: auto;
  margin-right: auto;
}

.toggle-btn {
  flex: 1;
  background: none;
  border: none;
  padding: 10px 15px;
  cursor: pointer;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.toggle-btn.active {
  background-color: #4CAF50;
  color: white;
}

@media (max-width: 768px) {
  .workflow-guide {
    flex-direction: column;
  }
  
  .workflow-step {
    margin-bottom: 10px;
  }
}
</style> 