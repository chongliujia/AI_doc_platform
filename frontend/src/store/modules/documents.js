import api from '@/services/api'

// 存储文档状态请求错误次数的对象
const documentErrorCounts = {}
// 最大尝试次数，超过这个次数将停止自动轮询
const MAX_ERROR_ATTEMPTS = 5

export default {
  namespaced: true,
  
  state: {
    documents: [],
    loading: false,
    error: null
  },
  
  mutations: {
    SET_DOCUMENTS(state, documents) {
      state.documents = documents
    },
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    SET_ERROR(state, error) {
      state.error = error
    },
    ADD_DOCUMENT(state, document) {
      state.documents.unshift(document)
    },
    UPDATE_DOCUMENT(state, updatedDocument) {
      const index = state.documents.findIndex(doc => doc.id === updatedDocument.id)
      if (index !== -1) {
        state.documents.splice(index, 1, updatedDocument)
      }
    }
  },
  
  actions: {
    async fetchDocuments({ commit }) {
      commit('SET_LOADING', true)
      try {
        const response = await api.getDocuments()
        commit('SET_DOCUMENTS', response.data)
        commit('SET_ERROR', null)
      } catch (error) {
        commit('SET_ERROR', '获取文档列表失败')
        console.error(error)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    async createDocument({ commit }, documentData) {
      try {
        const response = await api.createDocument(documentData)
        return response.data
      } catch (error) {
        console.error(error)
        throw error
      }
    },
    
    async createAdvancedDocument({ commit }, documentData) {
      try {
        const response = await api.createAdvancedDocument(documentData)
        return response.data
      } catch (error) {
        console.error(error)
        throw error
      }
    },
    
    async getDocument({ commit }, documentId) {
      try {
        const response = await api.getDocument(documentId)
        return response.data
      } catch (error) {
        console.error(error)
        throw error
      }
    },
    
    async getDocumentStatus({ commit }, documentId) {
      try {
        const response = await api.getDocumentStatus(documentId)
        // 成功后重置错误计数
        documentErrorCounts[documentId] = 0
        return response.data
      } catch (error) {
        // 如果是404错误，则增加错误计数
        if (error.response && error.response.status === 404) {
          if (!documentErrorCounts[documentId]) {
            documentErrorCounts[documentId] = 0
          }
          documentErrorCounts[documentId]++
          
          console.warn(`文档 ${documentId} 不存在，这是第 ${documentErrorCounts[documentId]} 次尝试`)
          
          // 如果超过最大尝试次数，则在错误中添加标记以便UI可以停止轮询
          if (documentErrorCounts[documentId] >= MAX_ERROR_ATTEMPTS) {
            error.stopPolling = true
            console.error(`已达到最大尝试次数(${MAX_ERROR_ATTEMPTS})，建议停止轮询`)
          }
        }
        
        console.error(`获取文档状态失败:`, error)
        throw error
      }
    },
    
    // 添加一个重置错误计数的方法，以便在需要时重新开始轮询
    resetErrorCount(_, documentId) {
      documentErrorCounts[documentId] = 0
    }
  },
  
  getters: {
    getDocumentById: (state) => (id) => {
      return state.documents.find(doc => doc.id === id)
    }
  }
} 