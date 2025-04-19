<template>
  <div class="outline-preview">
    <!-- 顶部标题区域 -->
    <div class="title-selection-section">
      <h2 class="section-title">标题选择</h2>
      <div class="title-options-container">
        <!-- 标题提示信息 -->
        <p class="help-text">从以下AI生成的标题中选择一个，或自定义您自己的标题：</p>
        
        <!-- 标题选择选项卡 -->
        <div class="title-options">
          <div 
            v-for="(title, index) in titleSuggestions" 
            :key="index" 
            :class="['title-option', { active: selectedTitle === title }]"
            @click="selectTitle(title)">
            {{ title }}
          </div>
          
          <!-- 自定义标题输入框 -->
          <div class="custom-title-input">
            <input 
              type="text" 
              v-model="customTitle" 
              placeholder="或输入自定义标题..." 
              @input="selectCustomTitle"
            />
          </div>
        </div>
      </div>
    </div>
    
    <h2 class="section-title">大纲预览</h2>
    
    <!-- 原有的大纲内容 -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>正在生成大纲...</p>
    </div>
    <div v-else class="outline-content">
      <draggable 
        v-model="localOutlineItems" 
        group="outlineItems" 
        handle=".drag-handle"
        @end="updateOrder"
        class="outline-tree">
        <div 
          v-for="(item, index) in localOutlineItems" 
          :key="item.id" 
          :class="['outline-item', `level-${item.level}`]">
          <div class="item-content">
            <span class="drag-handle">⠿</span>
            <div class="item-details">
              <input 
                type="text" 
                v-model="item.title" 
                :class="['title-input', `level-${item.level}`]"
                @change="updateItem(item)" 
              />
            </div>
            <div class="item-actions">
              <button @click="moveUp(index)" class="action-btn" :disabled="index === 0">上移</button>
              <button @click="moveDown(index)" class="action-btn" :disabled="index === localOutlineItems.length - 1">下移</button>
              <button @click="removeItem(item)" class="action-btn">删除</button>
              <button @click="addChildItem(item)" class="action-btn" v-if="item.level === 1">添加子项</button>
              <button @click="addSiblingItem(item)" class="action-btn">添加并列项</button>
            </div>
          </div>
        </div>
      </draggable>
      <div class="add-section">
        <button @click="addSection" class="primary-btn">添加新章节</button>
      </div>
    </div>
    
    <div class="actions">
      <button @click="goBack" class="secondary-btn">返回</button>
      <button @click="updateOutline" class="primary-btn" :disabled="loading">更新大纲</button>
      <button @click="confirmOutline" class="success-btn" :disabled="loading">确认大纲并生成文档</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import draggable from 'vuedraggable';

export default {
  components: {
    draggable
  },
  props: {
    previewId: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const router = useRouter();
    const route = useRoute();
    
    const loading = ref(true);
    const outlineItems = ref([]);
    const localOutlineItems = ref([]);
    const docType = ref('');
    const topic = ref('');
    
    // 标题相关数据
    const titleSuggestions = ref([]);
    const selectedTitle = ref('');
    const customTitle = ref('');
    const isCustomTitle = ref(false);
    
    // 监听自定义标题变化
    watch(customTitle, (newVal) => {
      if (isCustomTitle.value && newVal) {
        selectedTitle.value = newVal;
      }
    });
    
    // 选择标题
    const selectTitle = (title) => {
      selectedTitle.value = title;
      isCustomTitle.value = false;
    };
    
    // 选择自定义标题
    const selectCustomTitle = () => {
      selectedTitle.value = customTitle.value;
      isCustomTitle.value = true;
    };
    
    const fetchOutlinePreview = async () => {
      try {
        loading.value = true;
        const response = await axios.get(`/api/outline/${props.previewId}`);
        outlineItems.value = response.data.outline_items;
        localOutlineItems.value = [...response.data.outline_items];
        docType.value = response.data.doc_type;
        topic.value = response.data.topic;
        
        // 处理标题建议
        titleSuggestions.value = response.data.title_suggestions || [response.data.topic];
        selectedTitle.value = response.data.selected_title || response.data.topic;
      } catch (error) {
        console.error('获取大纲预览失败:', error);
      } finally {
        loading.value = false;
      }
    };
    
    const updateOutline = async () => {
      try {
        loading.value = true;
        await axios.put(`/api/outline/${props.previewId}`, {
          outline_items: localOutlineItems.value,
          selected_title: selectedTitle.value
        });
        await fetchOutlinePreview();
      } catch (error) {
        console.error('更新大纲失败:', error);
      } finally {
        loading.value = false;
      }
    };
    
    const confirmOutline = async () => {
      try {
        loading.value = true;
        const response = await axios.post(`/api/outline/${props.previewId}/confirm`, {
          selected_title: selectedTitle.value,
          template_id: route.query.template_id || null,
          max_pages: route.query.max_pages ? parseInt(route.query.max_pages) : null
        });
        router.push(`/document/${response.data.id}`);
      } catch (error) {
        console.error('确认大纲失败:', error);
        loading.value = false;
      }
    };
    
    const addSection = () => {
      const newId = `section_${Date.now()}`;
      localOutlineItems.value.push({
        id: newId,
        title: '新章节',
        level: 1,
        parent_id: null,
        order: localOutlineItems.value.length
      });
    };
    
    const addChildItem = (parentItem) => {
      const newId = `${parentItem.id}_child_${Date.now()}`;
      const parentIndex = localOutlineItems.value.findIndex(item => item.id === parentItem.id);
      
      // 查找当前父项下的所有子项
      const childItems = localOutlineItems.value.filter(item => item.parent_id === parentItem.id);
      const insertIndex = parentIndex + childItems.length + 1;
      
      localOutlineItems.value.splice(insertIndex, 0, {
        id: newId,
        title: '新子项',
        level: 2,
        parent_id: parentItem.id,
        order: childItems.length
      });
    };
    
    const addSiblingItem = (item) => {
      const level = item.level;
      const parentId = item.parent_id;
      const newId = `${level === 1 ? 'section' : 'child'}_${Date.now()}`;
      
      // 查找当前项的索引
      const itemIndex = localOutlineItems.value.findIndex(i => i.id === item.id);
      
      // 找出同一级别且同一父节点的所有项
      const siblingItems = localOutlineItems.value.filter(i => 
        i.level === level && i.parent_id === parentId
      );
      
      // 插入到当前项的后面
      localOutlineItems.value.splice(itemIndex + 1, 0, {
        id: newId,
        title: level === 1 ? '新章节' : '新子项',
        level: level,
        parent_id: parentId,
        order: siblingItems.length
      });
    };
    
    const removeItem = (item) => {
      // 如果是父项，同时移除所有子项
      if (item.level === 1) {
        localOutlineItems.value = localOutlineItems.value.filter(i => 
          i.id !== item.id && i.parent_id !== item.id
        );
      } else {
        localOutlineItems.value = localOutlineItems.value.filter(i => i.id !== item.id);
      }
      
      // 更新顺序
      updateOrder();
    };
    
    const moveUp = (index) => {
      if (index > 0) {
        const currentItem = localOutlineItems.value[index];
        const prevItem = localOutlineItems.value[index - 1];
        
        // 如果前一个项目是不同级别或不同父节点，则不移动
        if (currentItem.level !== prevItem.level || currentItem.parent_id !== prevItem.parent_id) {
          return;
        }
        
        // 交换位置
        [localOutlineItems.value[index - 1], localOutlineItems.value[index]] = 
        [localOutlineItems.value[index], localOutlineItems.value[index - 1]];
        
        // 更新顺序
        updateOrder();
      }
    };
    
    const moveDown = (index) => {
      if (index < localOutlineItems.value.length - 1) {
        const currentItem = localOutlineItems.value[index];
        const nextItem = localOutlineItems.value[index + 1];
        
        // 如果下一个项目是不同级别或不同父节点，则不移动
        if (currentItem.level !== nextItem.level || currentItem.parent_id !== nextItem.parent_id) {
          return;
        }
        
        // 交换位置
        [localOutlineItems.value[index], localOutlineItems.value[index + 1]] = 
        [localOutlineItems.value[index + 1], localOutlineItems.value[index]];
        
        // 更新顺序
        updateOrder();
      }
    };
    
    const updateOrder = () => {
      // 更新父项顺序
      const parentItems = localOutlineItems.value.filter(item => item.level === 1);
      parentItems.forEach((item, index) => {
        item.order = index;
      });
      
      // 更新每个父项下的子项顺序
      parentItems.forEach(parentItem => {
        const childItems = localOutlineItems.value.filter(item => 
          item.parent_id === parentItem.id
        );
        childItems.forEach((childItem, childIndex) => {
          childItem.order = childIndex;
        });
      });
    };
    
    const updateItem = (item) => {
      // 实时更新本地数据，不需要发送请求
      const index = localOutlineItems.value.findIndex(i => i.id === item.id);
      if (index !== -1) {
        localOutlineItems.value[index] = { ...item };
      }
    };
    
    const goBack = () => {
      router.back();
    };
    
    onMounted(() => {
      fetchOutlinePreview();
    });
    
    return {
      loading,
      outlineItems,
      localOutlineItems,
      docType,
      topic,
      titleSuggestions,
      selectedTitle,
      customTitle,
      isCustomTitle,
      selectTitle,
      selectCustomTitle,
      updateOutline,
      confirmOutline,
      addSection,
      addChildItem,
      addSiblingItem,
      removeItem,
      moveUp,
      moveDown,
      updateOrder,
      updateItem,
      goBack
    };
  }
};
</script>

<style scoped>
.outline-preview {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.section-title {
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: #333;
  border-bottom: 2px solid #eee;
  padding-bottom: 0.5rem;
}

/* 标题选择部分样式 */
.title-selection-section {
  margin-bottom: 30px;
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.title-options-container {
  margin-top: 10px;
}

.help-text {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 10px;
}

.title-options {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 15px;
}

.title-option {
  padding: 10px 15px;
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.95rem;
  min-width: 120px;
  text-align: center;
}

.title-option:hover {
  border-color: #4299e1;
  background-color: #ebf8ff;
}

.title-option.active {
  border-color: #4299e1;
  background-color: #ebf8ff;
  font-weight: bold;
  box-shadow: 0 2px 4px rgba(66, 153, 225, 0.15);
}

.custom-title-input {
  width: 100%;
  margin-top: 10px;
}

.custom-title-input input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.95rem;
}

.custom-title-input input:focus {
  border-color: #4299e1;
  outline: none;
  box-shadow: 0 0 0 2px rgba(66, 153, 225, 0.2);
}

/* 原有的大纲样式 */
.outline-content {
  margin-top: 20px;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top: 4px solid #3498db;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.outline-tree {
  margin-bottom: 20px;
}

.outline-item {
  margin-bottom: 8px;
  border-radius: 4px;
  overflow: hidden;
}

.level-1 {
  margin-left: 0;
  background-color: #f8f9fa;
}

.level-2 {
  margin-left: 30px;
  background-color: #f0f4f8;
}

.item-content {
  display: flex;
  align-items: center;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.drag-handle {
  cursor: move;
  margin-right: 10px;
  color: #999;
  font-size: 1.2rem;
}

.item-details {
  flex: 1;
}

.title-input {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.95rem;
}

.title-input.level-1 {
  font-weight: bold;
}

.item-actions {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.action-btn {
  font-size: 0.8rem;
  padding: 4px 8px;
  border: 1px solid #ddd;
  background-color: #f8f9fa;
  border-radius: 4px;
  cursor: pointer;
  white-space: nowrap;
}

.action-btn:hover {
  background-color: #e9ecef;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.add-section {
  margin-top: 20px;
  text-align: center;
}

.primary-btn, .secondary-btn, .success-btn {
  padding: 8px 16px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 500;
}

.primary-btn {
  background-color: #4299e1;
  color: white;
}

.primary-btn:hover {
  background-color: #3182ce;
}

.secondary-btn {
  background-color: #e2e8f0;
  color: #4a5568;
}

.secondary-btn:hover {
  background-color: #cbd5e0;
}

.success-btn {
  background-color: #48bb78;
  color: white;
}

.success-btn:hover {
  background-color: #38a169;
}

.actions {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}
</style> 