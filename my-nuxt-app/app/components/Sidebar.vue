<template>
  <aside class="sidebar">
    <div class="brand-logo">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
      </svg>
      <div class="brand-text">
        <span class="title-en">AI Intervention</span>
        <span class="title-cn">智能风险预警系统</span>
      </div>
    </div>

    <div class="menu-container">
      <el-menu :default-active="defaultActive" class="custom-el-menu" :unique-opened="true">
        <div class="menu-group-title">DATA PIPELINE 数据管道</div>
        <el-sub-menu index="1">
          <template #title><el-icon><Coin /></el-icon><span>数据接入与特征工程</span></template>
          <el-menu-item index="1-1" @click="goTo('/datainput')">职业暴露特征录入</el-menu-item>
          <el-menu-item index="1-2">外部 LIS 系统接口</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="2">
          <template #title><el-icon><DataLine /></el-icon><span>数据集智能治理</span></template>
          <el-menu-item index="2-1">缺失值与异常清洗</el-menu-item>
          <el-menu-item index="2-2">特征降维与标准化</el-menu-item>
        </el-sub-menu>

        <div class="menu-group-title">MODEL LAYER 模型层</div>
        <el-sub-menu index="3">
          <template #title><el-icon><TrendCharts /></el-icon><span>风险量化与预警</span></template>
          <el-menu-item index="3-1" @click="goTo('/risk')">个体靶器官预警</el-menu-item>
          <el-menu-item index="3-2">群体风险热力图</el-menu-item>
        </el-sub-menu>
        
        <el-menu-item index="4" @click="goTo('/causal')">
          <el-icon><Share /></el-icon><span>因果知识推理</span>
        </el-menu-item>
        
        <el-menu-item index="5" @click="goTo('/plan')">
          <el-icon><DocumentChecked /></el-icon><span>智能干预策略推荐</span>
        </el-menu-item>
        
        <div class="menu-group-title">KNOWLEDGE BASE 知识库</div>
        <el-menu-item index="6" @click="goTo('/agent')">
          <el-icon><ChatDotRound /></el-icon><span>AI 知识库助手</span>
        </el-menu-item>
      </el-menu>
    </div>
  </aside>
</template>

<script setup>
import { 
  Coin, DataLine, TrendCharts, Share, DocumentChecked, ChatDotRound 
} from '@element-plus/icons-vue'

// 定义 props 接收父组件（各个页面）传来的激活项 index
defineProps({
  defaultActive: {
    type: String,
    required: true,
    default: '1-1'
  }
})

const router = useRouter()

// 统一的路由跳转方法（避免与 Nuxt 自动导入的 navigateTo 冲突）
const goTo = (path) => {
  router.push(path)
}
</script>

<style lang="scss" scoped>
/* 侧边栏专属局部变量，保证独立组件色彩精确 */
$c-primary: #1f77b4;
$c-primary-light: #EFF6FF;
$border-light: #E2E8F0;

* { box-sizing: border-box; }

.sidebar { 
  width: 280px; 
  background-color: #fff; 
  border-right: 1px solid $border-light; 
  display: flex; 
  flex-direction: column; 
  z-index: 10; 
  flex-shrink: 0; 
  box-shadow: 2px 0 15px rgba(0,0,0,0.03); 
  height: 100%; /* 占满父容器高度 */
}

.brand-logo { 
  height: 70px; 
  display: flex; 
  align-items: center; 
  gap: 14px; 
  padding: 0 24px; 
  border-bottom: 1px solid $border-light; 
  svg { 
    width: 30px; 
    height: 30px; 
    color: #2563EB; 
    flex-shrink: 0; 
  } 
  .brand-text { 
    display: flex; 
    flex-direction: column; 
  } 
  .title-en { 
    font-size: 1.1rem; 
    font-weight: 900; 
    color: #111827; 
    letter-spacing: -0.5px;
  } 
  .title-cn { 
    font-size: 0.8rem; 
    font-weight: 600; 
    color: #64748B; 
    letter-spacing: 1px; 
    margin-top: 2px;
  } 
}

.menu-container { 
  overflow-y: auto; 
  flex: 1; 
  padding: 16px 0; 
  
  /* 隐藏滚动条让视觉更干净 */
  &::-webkit-scrollbar { width: 0; }
  
  :deep(.custom-el-menu) { 
    border-right: none; 
    
    .menu-group-title { 
      font-size: 0.85rem; 
      font-weight: 800; 
      color: #94A3B8; 
      padding: 24px 24px 10px 24px; 
      letter-spacing: 1px;
    } 
    
    .el-menu-item { 
      font-weight: 600; 
      color: #475569; 
      font-size: 1.05rem; 
      margin: 6px 12px; 
      border-radius: 8px; 
      height: 50px; 
      transition: all 0.2s ease;
    } 
    
    .el-menu-item:hover { 
      background-color: #F8FAFC; 
      color: $c-primary; 
    } 
    
    .el-menu-item.is-active { 
      background-color: $c-primary-light; 
      color: #2563EB; 
      font-weight: 700;
    } 
    
    /* 修复下拉菜单标题样式 */
    .el-sub-menu__title {
      font-weight: 600; 
      color: #475569; 
      font-size: 1.05rem;
      margin: 0 12px;
      border-radius: 8px;
      height: 50px;
      transition: all 0.2s ease;
      &:hover {
        background-color: #F8FAFC; 
        color: $c-primary;
      }
    }
  } 
}
</style>
