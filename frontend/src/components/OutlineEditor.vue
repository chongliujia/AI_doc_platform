<template>
  <div class="outline-editor">
    <h2 class="editor-title">{{ title || '文档大纲' }}</h2>
    
    <div class="editor-actions mb-4">
      <div class="topic-input-container">
        <label for="topic-input" class="form-label">文档主题</label>
        <input 
          id="topic-input"
          v-model="topicInput" 
          class="form-control" 
          type="text" 
          placeholder="请输入文档主题" 
        />
      </div>
      
      <div class="action-buttons">
        <button 
          class="btn btn-outline-primary save-btn" 
          @click="saveOutline"
          :disabled="isSaving"
        >
          <i class="fa fa-save"></i> {{ isSaving ? '保存中...' : '保存大纲' }}
        </button>
        <button 
          class="btn btn-success confirm-btn" 
          @click="confirmOutline"
          :disabled="isConfirming"
        >
          <i class="fa fa-check-circle"></i> {{ isConfirming ? '处理中...' : '确认大纲并生成文档' }}
        </button>
      </div>
      
      <div class="step-indicator">
        <span class="step-number">3</span>
        <span class="step-description">确认后将生成完整文档</span>
      </div>
    </div>
    
    <div class="outline-items-container">
      <h3 class="section-title">章节目录</h3>
      
      <div class="outline-items">
        <draggable 
          v-model="items" 
          group="outline" 
          @end="reorderItems" 
          handle=".drag-handle"
        >
          <div 
            v-for="item in items" 
            :key="item.id" 
            class="outline-item"
            :class="{ 'level-2': item.level === 2 }"
          >
            <div class="item-header">
              <i class="drag-handle fa fa-grip-vertical"></i>
              <input 
                v-model="item.title" 
                class="form-control" 
                type="text"
                @change="itemChanged(item)"
              />
              <div class="item-actions">
                <button class="btn btn-sm btn-icon" @click="removeItem(item)" title="删除">
                  <i class="fa fa-trash"></i>
                </button>
                <button 
                  v-if="item.level === 1" 
                  class="btn btn-sm btn-icon btn-add" 
                  @click="addSubItem(item)"
                  title="添加子项"
                >
                  <i class="fa fa-plus"></i>
                </button>
              </div>
            </div>
          </div>
        </draggable>
        
        <div class="add-item-actions">
          <button class="btn btn-outline-primary add-chapter-btn" @click="addMainItem">
            <i class="fa fa-plus"></i> 添加主章节
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// 替代uuid库的简单函数
function generateId() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

import draggable from 'vuedraggable';
import api from '../services/api';

export default {
  name: 'OutlineEditor',
  components: {
    draggable
  },
  props: {
    outlineId: {
      type: String,
      required: true
    },
    initialItems: {
      type: Array,
      default: () => []
    },
    initialTopic: {
      type: String,
      default: ''
    },
    title: {
      type: String,
      default: ''
    },
    maxPages: {
      type: Number,
      default: 0
    }
  },
  data() {
    return {
      items: [],
      topicInput: this.initialTopic,
      isSaving: false,
      isConfirming: false
    };
  },
  created() {
    // 复制初始项目，避免修改props
    this.items = JSON.parse(JSON.stringify(this.initialItems));
  },
  methods: {
    addMainItem() {
      // 获取当前主项目的最大顺序
      const maxOrder = this.items
        .filter(item => item.level === 1)
        .reduce((max, item) => Math.max(max, item.order), 0);
      
      // 创建新主项目
      const newItem = {
        id: generateId(),
        title: '新章节',
        level: 1,
        parent_id: null,
        order: maxOrder + 1
      };
      
      this.items.push(newItem);
      this.reorderItems();
    },
    
    addSubItem(parent) {
      // 获取当前父项下子项的最大顺序
      const maxOrder = this.items
        .filter(item => item.parent_id === parent.id)
        .reduce((max, item) => Math.max(max, item.order), 0);
      
      // 创建新子项
      const newItem = {
        id: generateId(),
        title: '新子章节',
        level: 2,
        parent_id: parent.id,
        order: maxOrder + 1
      };
      
      // 找到父项的位置并在其后添加子项
      const parentIndex = this.items.findIndex(item => item.id === parent.id);
      
      // 找到最后一个属于该父项的子项的位置
      let lastChildIndex = parentIndex;
      for (let i = parentIndex + 1; i < this.items.length; i++) {
        if (this.items[i].parent_id === parent.id) {
          lastChildIndex = i;
        } else if (this.items[i].level === 1) {
          break;
        }
      }
      
      // 在最后一个子项后插入新子项
      this.items.splice(lastChildIndex + 1, 0, newItem);
      this.reorderItems();
    },
    
    removeItem(item) {
      // 如果是主项，也需要删除其所有子项
      if (item.level === 1) {
        this.items = this.items.filter(i => i.id !== item.id && i.parent_id !== item.id);
      } else {
        this.items = this.items.filter(i => i.id !== item.id);
      }
      
      this.reorderItems();
    },
    
    itemChanged(item) {
      // 当项目内容变更时可以执行一些逻辑
      this.$emit('item-changed', item);
    },
    
    reorderItems() {
      // 重新排序并确保子项紧跟在父项后面
      const mainItems = this.items
        .filter(item => item.level === 1)
        .sort((a, b) => a.order - b.order);
      
      const newItems = [];
      
      mainItems.forEach((mainItem, index) => {
        // 更新主项顺序
        mainItem.order = index + 1;
        newItems.push(mainItem);
        
        // 添加子项
        const subItems = this.items
          .filter(item => item.parent_id === mainItem.id)
          .sort((a, b) => a.order - b.order);
        
        subItems.forEach((subItem, subIndex) => {
          subItem.order = subIndex + 1;
          newItems.push(subItem);
        });
      });
      
      this.items = newItems;
      this.$emit('items-reordered', this.items);
    },
    
    async saveOutline() {
      this.isSaving = true;
      
      try {
        const response = await api.updateOutlinePreview(this.outlineId, {
          outline_items: this.items,
          topic: this.topicInput
        });
        
        this.$emit('outline-saved', response.data);
        this.$emit('update:initialTopic', this.topicInput);
        this.$emit('update:initialItems', this.items);
        
        // 显示成功消息
        this.$toast.success('大纲已保存');
      } catch (error) {
        console.error('保存大纲失败:', error);
        this.$toast.error('保存大纲失败：' + (error.response && error.response.data && error.response.data.detail || error.message));
      } finally {
        this.isSaving = false;
      }
    },
    
    async confirmOutline() {
      // 先保存当前大纲
      await this.saveOutline();
      
      this.isConfirming = true;
      
      try {
        // 确认大纲，并传递模板ID（如果需要）
        const confirmData = {
          preview_id: this.outlineId,
          template_id: 'default', // 可以从props或其他地方获取模板ID
          max_pages: this.maxPages // 添加页数限制参数
        };
        
        const response = await api.confirmOutline(confirmData);
        
        this.$emit('outline-confirmed', response.data);
      } catch (error) {
        console.error('确认大纲失败:', error);
        this.$toast.error('确认大纲失败：' + (error.response && error.response.data && error.response.data.detail || error.message));
      } finally {
        this.isConfirming = false;
      }
    }
  }
};
</script>

<style scoped>
.outline-editor {
  background-color: #ffffff;
  border-radius: 12px;
  padding: 30px;
  margin-bottom: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.editor-title {
  font-size: 24px;
  color: #333;
  margin-bottom: 25px;
  border-bottom: 2px solid #f0f0f0;
  padding-bottom: 15px;
}

.topic-input-container {
  margin-bottom: 20px;
}

.form-label {
  font-weight: 600;
  display: block;
  margin-bottom: 8px;
  color: #555;
}

.action-buttons {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
}

.save-btn, .confirm-btn {
  padding: 10px 20px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.confirm-btn {
  background-color: #2e7d32;
  border: none;
  padding: 12px 25px;
  flex-grow: 1;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.confirm-btn:hover:not(:disabled) {
  background-color: #1b5e20;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.section-title {
  font-size: 18px;
  color: #444;
  margin: 20px 0 15px;
  font-weight: 600;
}

.outline-items-container {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  background-color: #fafafa;
}

.outline-items {
  max-height: 500px;
  overflow-y: auto;
  padding: 10px 0;
}

.outline-item {
  background-color: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  margin-bottom: 12px;
  padding: 12px;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.outline-item:hover {
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.1);
  border-color: #bbdefb;
}

.level-2 {
  margin-left: 40px;
  border-left: 3px solid #2196F3;
  background-color: #f5f9ff;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.item-header input {
  flex-grow: 1;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 15px;
}

.item-header input:focus {
  border-color: #2196F3;
  box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.2);
  outline: none;
}

.item-actions {
  display: flex;
  gap: 8px;
}

.btn-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #757575;
  background-color: #f5f5f5;
  border: 1px solid #e0e0e0;
  transition: all 0.2s ease;
}

.btn-icon:hover {
  background-color: #eeeeee;
  color: #333;
}

.btn-icon i {
  font-size: 16px;
}

.btn-add {
  color: #2196F3;
  background-color: #e3f2fd;
  border-color: #bbdefb;
}

.btn-add:hover {
  background-color: #bbdefb;
  color: #0d47a1;
}

.drag-handle {
  cursor: move;
  color: #9e9e9e;
  padding: 0 5px;
  font-size: 18px;
}

.drag-handle:hover {
  color: #616161;
}

.add-item-actions {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.add-chapter-btn {
  padding: 10px 25px;
  color: #2196F3;
  border-color: #2196F3;
  border-width: 2px;
  font-weight: 600;
}

.add-chapter-btn:hover {
  background-color: #e3f2fd;
  border-color: #1e88e5;
  color: #1565c0;
}

.step-indicator {
  display: flex;
  align-items: center;
  margin-top: 15px;
  color: #2e7d32;
  font-weight: 600;
  background-color: #e8f5e9;
  padding: 10px 15px;
  border-radius: 6px;
}

.step-number {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  width: 28px;
  height: 28px;
  background-color: #2e7d32;
  color: white;
  border-radius: 50%;
  margin-right: 12px;
  font-weight: bold;
}

.step-description {
  font-size: 15px;
}
</style> 