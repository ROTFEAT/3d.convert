<?php
/*
Template Name: 文件转换工具（单文件版）
*/
get_header();

/* ===== 解析 slug ===== */
$slug = get_query_var('convert_slug');                 // stl-to-step
if (preg_match('/^([a-z0-9]+)-to-([a-z0-9]+)$/', $slug, $m)) {
    $from = strtoupper($m[1]);
    $to   = strtoupper($m[2]);
} else {
    $from = $to = null;
}
?>
<?php if ($from && $to): ?>
    <title><?php echo "{$from} 转 {$to} 在线转换 | FabRapid"; ?></title>
    <meta name="description" content="免费在线将 <?php echo $from; ?> 转为 <?php echo $to; ?>；云端处理、无需安装软件。">
<?php endif; ?>

<style>
/* ===== 品牌色彩变量 ===== */
:root {
    --brand-blue: #0171E2;
    --brand-blue-hover: #0056b3;
    --brand-blue-light: #e6f3ff;
    --success-green: #10b981;
    --error-red: #ef4444;
    --warning-orange: #f59e0b;
    --gray-50: #f9fafb;
    --gray-100: #f3f4f6;
    --gray-200: #e5e7eb;
    --gray-300: #d1d5db;
    --gray-400: #9ca3af;
    --gray-500: #6b7280;
    --gray-600: #4b5563;
    --gray-700: #374151;
    --gray-800: #1f2937;
    --gray-900: #111827;
}

.fr-hidden { display: none; }

.fr-main-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem 1rem;
    display: grid;
    grid-template-columns: 1fr 300px;
    gap: 2rem;
    align-items: start;
}

.fr-tool-section {
    background: white;
    border-radius: 12px;
    border: 1px solid var(--gray-200);
    overflow: hidden;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.fr-tool-header {
    background: var(--gray-50);
    padding: 1.5rem;
    border-bottom: 1px solid var(--gray-200);
}

.fr-tool-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--gray-800);
    margin: 0 0 0.5rem 0;
}

.fr-tool-desc {
    color: var(--gray-500);
    font-size: 0.875rem;
    margin: 0;
}

.fr-tool-body {
    padding: 1.5rem;
}

/* 上传区域 */
.fr-upload-zone {
    border: 2px dashed var(--gray-300);
    border-radius: 8px;
    padding: 2rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s ease;
    background: var(--gray-50);
}

.fr-upload-zone:hover {
    border-color: var(--brand-blue);
    background: var(--brand-blue-light);
}

.fr-upload-icon {
    width: 2.5rem;
    height: 2.5rem;
    color: var(--gray-400);
    margin: 0 auto 0.75rem;
}

.fr-upload-zone:hover .fr-upload-icon {
    color: var(--brand-blue);
}

.fr-upload-text {
    font-weight: 500;
    color: var(--gray-700);
    margin-bottom: 0.25rem;
}

.fr-upload-hint {
    font-size: 0.75rem;
    color: var(--gray-400);
}

/* 文件信息 */
.fr-file-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    background: var(--gray-50);
    border-radius: 8px;
    margin-bottom: 1.5rem;
}

.fr-file-icon {
    width: 2.5rem;
    height: 2.5rem;
    background: var(--brand-blue);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    flex-shrink: 0;
}

.fr-file-details {
    flex: 1;
    min-width: 0;
}

.fr-file-name {
    font-weight: 500;
    color: var(--gray-800);
    font-size: 0.875rem;
    margin: 0 0 0.125rem 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.fr-file-size {
    font-size: 0.75rem;
    color: var(--gray-500);
    margin: 0;
}

/* 格式选择 */
.fr-format-section {
    margin-bottom: 1.5rem;
}

.fr-format-label {
    display: block;
    font-weight: 500;
    color: var(--gray-700);
    font-size: 0.875rem;
    margin-bottom: 0.5rem;
}

.fr-format-select {
    width: 100%;
    padding: 0.75rem 1rem;
    border: 1px solid var(--gray-300);
    border-radius: 6px;
    font-size: 0.875rem;
    background: white;
    transition: border-color 0.2s ease;
}

.fr-format-select:focus {
    outline: none;
    border-color: var(--brand-blue);
    box-shadow: 0 0 0 3px rgba(1, 113, 226, 0.1);
}

/* 按钮区域 */
.fr-actions {
    display: flex;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
}

.fr-btn {
    flex: 1;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    font-weight: 500;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s ease;
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.fr-btn-primary {
    background: var(--brand-blue);
    color: white;
}

.fr-btn-primary:hover:not(:disabled) {
    background: var(--brand-blue-hover);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(1, 113, 226, 0.3);
}

.fr-btn-primary:disabled {
    background: var(--gray-400);
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
}

.fr-btn-secondary {
    background: white;
    color: var(--gray-700);
    border: 1px solid var(--gray-300);
}

.fr-btn-secondary:hover {
    background: var(--gray-50);
    border-color: var(--gray-400);
}

/* 进度区域 - 重新设计 */
.fr-progress-section {
    background: var(--gray-50);
    border-radius: 8px;
    padding: 1.5rem;
    border: 1px solid var(--gray-200);
}

/* 步骤指示器 - 现代化设计 */
.fr-steps {
    display: flex;
    justify-content: space-between;
    margin-bottom: 2rem;
    position: relative;
}

.fr-steps::before {
    content: '';
    position: absolute;
    top: 1.25rem;
    left: 1.25rem;
    right: 1.25rem;
    height: 2px;
    background: var(--gray-200);
    z-index: 1;
}

.fr-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    z-index: 2;
    flex: 1;
}

.fr-step-circle {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 50%;
    background: white;
    border: 2px solid var(--gray-200);
    color: var(--gray-400);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.875rem;
    margin-bottom: 0.75rem;
    transition: all 0.3s ease;
}

.fr-step.active .fr-step-circle {
    background: var(--brand-blue);
    border-color: var(--brand-blue);
    color: white;
    animation: pulse-glow 2s infinite;
}

.fr-step.completed .fr-step-circle {
    background: var(--success-green);
    border-color: var(--success-green);
    color: white;
}

.fr-step-label {
    font-size: 0.75rem;
    color: var(--gray-500);
    text-align: center;
    font-weight: 500;
}

.fr-step.active .fr-step-label {
    color: var(--brand-blue);
    font-weight: 600;
}

.fr-step.completed .fr-step-label {
    color: var(--success-green);
    font-weight: 600;
}

/* 现代化进度条 */
.fr-progress-bar-container {
    margin-bottom: 1.5rem;
}

.fr-progress-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.fr-progress-label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--gray-700);
}

.fr-progress-percent {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--brand-blue);
}

.fr-progress-track {
    height: 8px;
    background: var(--gray-200);
    border-radius: 4px;
    overflow: hidden;
    position: relative;
}

.fr-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--brand-blue) 0%, #4a9eff 100%);
    border-radius: 4px;
    transition: width 0.5s ease;
    width: 0%;
    position: relative;
}

.fr-progress-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%);
    animation: shimmer 2s infinite;
}

/* 状态消息 */
.fr-status-card {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    border-radius: 6px;
    background: white;
    border: 1px solid var(--gray-200);
}

.fr-status-card.info {
    background: var(--brand-blue-light);
    border-color: rgba(1, 113, 226, 0.2);
    color: var(--brand-blue);
}

.fr-status-card.success {
    background: #ecfdf5;
    border-color: rgba(16, 185, 129, 0.2);
    color: var(--success-green);
}

.fr-status-card.error {
    background: #fef2f2;
    border-color: rgba(239, 68, 68, 0.2);
    color: var(--error-red);
}

.fr-status-icon {
    width: 1.25rem;
    height: 1.25rem;
    flex-shrink: 0;
}

.fr-status-text {
    font-size: 0.875rem;
    font-weight: 500;
    flex: 1;
}

.fr-spinning {
    animation: spin 1s linear infinite;
}

/* 下载按钮 */
.fr-download-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: var(--success-green);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.875rem;
    transition: all 0.2s ease;
    margin-left: auto;
}

.fr-download-btn:hover {
    background: #059669;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

/* 侧边栏保持不变 */
.fr-sidebar {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.fr-info-card {
    background: white;
    border: 1px solid var(--gray-200);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.fr-info-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--gray-800);
    margin: 0 0 1rem 0;
}

.fr-info-content {
    font-size: 0.875rem;
    color: var(--gray-500);
    line-height: 1.5;
}

.fr-info-content p {
    margin: 0 0 0.75rem 0;
}

.fr-info-content p:last-child {
    margin-bottom: 0;
}

.fr-cta-btn {
    display: inline-block;
    background: var(--brand-blue);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.875rem;
    text-align: center;
    transition: all 0.2s ease;
    margin-top: 1rem;
}

.fr-cta-btn:hover {
    background: var(--brand-blue-hover);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(1, 113, 226, 0.3);
}

.fr-features {
    list-style: none;
    padding: 0;
    margin: 0;
}

.fr-features li {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
    color: var(--gray-500);
}

.fr-features li:last-child {
    margin-bottom: 0;
}

.fr-check-icon {
    width: 1rem;
    height: 1rem;
    color: var(--success-green);
    flex-shrink: 0;
}
.main-page-wrapper a {
    color: white;
}
/* 动画 */
@keyframes pulse-glow {
    0%, 100% { 
        transform: scale(1);
        box-shadow: 0 0 0 0 rgba(1, 113, 226, 0.4);
    }
    50% { 
        transform: scale(1.05);
        box-shadow: 0 0 0 8px rgba(1, 113, 226, 0);
    }
}

@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

/* 响应式 */
@media (max-width: 768px) {
    .fr-main-container {
        grid-template-columns: 1fr;
        gap: 1.5rem;
        padding: 1rem;
    }
    
    .fr-sidebar {
        order: -1;
    }
    
    .fr-actions {
        flex-direction: column;
    }
    
    .fr-steps {
        flex-wrap: wrap;
        gap: 1rem;
    }
    
    .fr-step {
        flex: none;
        min-width: 0;
    }
}
</style>

<main class="container">
<?php if (!$from || !$to): ?>
    <div class="fr-main-container" style="grid-template-columns: 1fr;">
        <div class="fr-tool-section">
            <div class="fr-tool-header">
                <h1 class="fr-tool-title">格式转换工具</h1>
                <p class="fr-tool-desc">路径不正确，请访问正确的转换页面</p>
            </div>
        </div>
    </div>
<?php else: ?>
    <div class="fr-main-container">
        <!-- 主工具区域 -->
        <div class="fr-tool-section">
            <div class="fr-tool-header">
                <h1 class="fr-tool-title"><?php echo "{$from} 转 {$to}"; ?></h1>
                <p class="fr-tool-desc">免费在线文件格式转换，云端处理，安全快速</p>
            </div>
            
            <div class="fr-tool-body">
                <div id="convert-app"
                     data-api="https://convertapi.pinplus.online"
                     data-to="<?php echo strtolower($to); ?>">
                    <!-- 加载中 -->
                    <div class="text-center py-4">
                        <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                        <p class="mt-2 text-sm text-gray-600">工具加载中…</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 侧边栏 - 公司信息 -->
        <div class="fr-sidebar">
            <!-- 关于我们 -->
            <div class="fr-info-card">
                <h3 class="fr-info-title">关于 FabRapid</h3>
                <div class="fr-info-content">
                    <p>FabRapid 是专业的制造服务平台，提供3D打印、CNC加工、注塑成型等一站式制造解决方案。</p>
                    <ul class="fr-features">
                        <li>
                            <svg class="fr-check-icon" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                            </svg>
                            快速报价，1小时内响应
                        </li>
                        <li>
                            <svg class="fr-check-icon" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                            </svg>
                            支持100+种材料
                        </li>
                        <li>
                            <svg class="fr-check-icon" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                            </svg>
                            ISO 9001质量认证
                        </li>
                    </ul>
                    <a href="/quote" class="fr-cta-btn">立即获取报价</a>
                </div>
            </div>
            
            <!-- 服务优势 -->
            <div class="fr-info-card">
                <h3 class="fr-info-title">为什么选择我们？</h3>
                <div class="fr-info-content">
                    <p><strong>专业团队</strong><br>10年制造经验，服务过1000+客户</p>
                    <p><strong>品质保证</strong><br>严格质检流程，不合格免费重做</p>
                    <p><strong>快速交付</strong><br>标准件3天交付，复杂件7天内完成</p>
                </div>
            </div>
            
            <!-- 联系方式 -->
            <div class="fr-info-card">
                <h3 class="fr-info-title">需要帮助？</h3>
                <div class="fr-info-content">
                    <p>我们的专业团队随时为您提供技术支持和咨询服务。</p>
                    <p><strong>客服热线：</strong>400-123-4567</p>
                    <p><strong>邮箱：</strong>support@fabrapid.com</p>
                    <p><strong>工作时间：</strong>周一至周五 9:00-18:00</p>
                </div>
            </div>
        </div>
    </div>
<?php endif; ?>
</main>

<script>
/* ===== 精简 JS ===== */
(function(){
  const app = document.getElementById('convert-app');
  if(!app) return;
  const API = app.dataset.api;
  const DEF_TO = app.dataset.to;

  const STEPS = [
    { id: 'upload', label: '上传文件', icon: '1' },
    { id: 'queue', label: '排队等待', icon: '2' },
    { id: 'process', label: '转换处理', icon: '3' },
    { id: 'complete', label: '完成下载', icon: '4' }
  ];

  app.innerHTML = `
    <input type="file" id="fr-file" class="fr-hidden">
    
    <!-- 上传区域 -->
    <div id="fr-upload" class="fr-upload-zone">
      <svg class="fr-upload-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
      </svg>
      <div class="fr-upload-text">点击选择文件或拖拽到此处</div>
      <div class="fr-upload-hint">支持多种格式，最大 100MB</div>
    </div>
    
    <!-- 处理区域 -->
    <div id="fr-process" class="fr-hidden">
      <!-- 文件信息 -->
      <div class="fr-file-info">
        <div class="fr-file-icon">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"/>
          </svg>
        </div>
        <div class="fr-file-details">
          <h4 class="fr-file-name" id="fr-filename">文件名</h4>
          <p class="fr-file-size" id="fr-filesize">文件大小</p>
        </div>
      </div>
      
      <!-- 格式选择 -->
      <div class="fr-format-section">
        <label class="fr-format-label">选择输出格式：</label>
        <select id="fr-format" class="fr-format-select">
          <option value="">加载中...</option>
        </select>
      </div>
      
      <!-- 操作按钮 -->
      <div class="fr-actions">
        <button id="fr-convert" class="fr-btn fr-btn-primary">
          开始转换
        </button>
        <button id="fr-reset" class="fr-btn fr-btn-secondary">重新选择</button>
      </div>
      
      <!-- 进度区域 -->
      <div id="fr-progress-section" class="fr-progress-section fr-hidden">
        <!-- 步骤指示器 -->
        <div class="fr-steps">
          ${STEPS.map(step => `
            <div class="fr-step" data-step="${step.id}">
              <div class="fr-step-circle">${step.icon}</div>
              <div class="fr-step-label">${step.label}</div>
            </div>
          `).join('')}
        </div>
        
        <!-- 进度条 -->
        <div class="fr-progress-bar-container">
          <div class="fr-progress-info">
            <span class="fr-progress-label" id="fr-progress-label">准备开始...</span>
            <span class="fr-progress-percent" id="fr-progress-percent">0%</span>
          </div>
          <div class="fr-progress-track">
            <div id="fr-progress-fill" class="fr-progress-fill"></div>
          </div>
        </div>
        
        <!-- 状态消息 -->
        <div id="fr-status-card" class="fr-status-card info">
          <svg class="fr-status-icon fr-spinning" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>
          </svg>
          <span class="fr-status-text" id="fr-status-text">准备开始转换...</span>
        </div>
      </div>
    </div>
  `;

  const $ = id => document.getElementById(id);
  const fileInput = $('fr-file');
  const formatSelect = $('fr-format');
  const progressFill = $('fr-progress-fill');
  const progressLabel = $('fr-progress-label');
  const progressPercent = $('fr-progress-percent');
  const statusCard = $('fr-status-card');
  const statusText = $('fr-status-text');
  
  let currentFile = null;
  let pollInterval = null;

  // 工具函数
  const formatFileSize = bytes => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const updateStep = (stepId, status = 'active') => {
    document.querySelectorAll('.fr-step').forEach(step => {
      step.classList.remove('active', 'completed');
    });
    
    const stepIndex = STEPS.findIndex(s => s.id === stepId);
    STEPS.forEach((step, index) => {
      const stepEl = document.querySelector(`[data-step="${step.id}"]`);
      if (index < stepIndex) {
        stepEl.classList.add('completed');
      } else if (index === stepIndex && status === 'active') {
        stepEl.classList.add('active');
      } else if (index === stepIndex && status === 'completed') {
        stepEl.classList.add('completed');
      }
    });
  };

  const updateProgress = (percent, message, type = 'info') => {
    progressFill.style.width = percent + '%';
    progressLabel.textContent = message;
    progressPercent.textContent = percent + '%';
    statusText.textContent = message;
    
    statusCard.className = `fr-status-card ${type}`;
    
    const iconEl = statusCard.querySelector('svg');
    if (type === 'success') {
      iconEl.innerHTML = '<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>';
      iconEl.classList.remove('fr-spinning');
    } else if (type === 'error') {
      iconEl.innerHTML = '<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>';
      iconEl.classList.remove('fr-spinning');
    } else {
      iconEl.innerHTML = '<path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>';
      iconEl.classList.add('fr-spinning');
    }
  };

  const resetApp = () => {
    fileInput.value = '';
    currentFile = null;
    $('fr-upload').classList.remove('fr-hidden');
    $('fr-process').classList.add('fr-hidden');
    $('fr-progress-section').classList.add('fr-hidden');
    if (pollInterval) {
      clearInterval(pollInterval);
      pollInterval = null;
    }
  };

  // 事件绑定
  $('fr-upload').onclick = () => fileInput.click();
  $('fr-reset').onclick = resetApp;

  fileInput.onchange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    currentFile = file;
    $('fr-filename').textContent = file.name;
    $('fr-filesize').textContent = formatFileSize(file.size);
    
    $('fr-upload').classList.add('fr-hidden');
    $('fr-process').classList.remove('fr-hidden');
  };

  // 拖拽支持
  $('fr-upload').ondragover = (e) => {
    e.preventDefault();
    e.currentTarget.style.borderColor = 'var(--brand-blue)';
    e.currentTarget.style.background = 'var(--brand-blue-light)';
  };
  
  $('fr-upload').ondragleave = (e) => {
    e.preventDefault();
    e.currentTarget.style.borderColor = 'var(--gray-300)';
    e.currentTarget.style.background = 'var(--gray-50)';
  };
  
  $('fr-upload').ondrop = (e) => {
    e.preventDefault();
    e.currentTarget.style.borderColor = 'var(--gray-300)';
    e.currentTarget.style.background = 'var(--gray-50)';
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      fileInput.files = files;
      fileInput.onchange({ target: { files } });
    }
  };

  // 开始转换
  $('fr-convert').onclick = async () => {
    if (!currentFile) {
      alert('请先选择文件');
      return;
    }
    
    const outputFormat = formatSelect.value;
    if (!outputFormat) {
      alert('请选择输出格式');
      return;
    }

    $('fr-progress-section').classList.remove('fr-hidden');
    $('fr-convert').disabled = true;
    
    try {
      updateStep('upload');
      updateProgress(10, '正在上传文件到云端...', 'info');
      
      const path = `uploads/${Date.now()}_${encodeURIComponent(currentFile.name)}`;
      const uploadResponse = await fetch(`${API}/r2/generate-upload-url?path=${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const uploadData = await uploadResponse.json();
      
      updateProgress(10, '正在传输文件数据...', 'info');
      
      await fetch(uploadData.data.upload_url, {
        method: 'PUT',
        body: currentFile,
        headers: { 'Content-Type': 'application/octet-stream' }
      });
      
      updateStep('queue');
      updateProgress(15, '文件上传完成，创建转换任务...', 'info');
      
      const formData = new FormData();
      formData.append('file_url', uploadData.data.download_url);
      formData.append('output_format', outputFormat);
      
      const convertResponse = await fetch(`${API}/convert`, {
        method: 'POST',
        body: formData
      });
      const convertData = await convertResponse.json();
      
      updateProgress(40, '转换任务已创建，正在排队处理...', 'info');
      
      pollTaskStatus(convertData.data.task_id);
      
    } catch (error) {
      updateProgress(0, `转换失败: ${error.message}`, 'error');
      $('fr-convert').disabled = false;
    }
  };

  // 轮询任务状态
  const pollTaskStatus = (taskId) => {
    pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API}/convert/${taskId}`);
        const data = await response.json();
        const status = data.data.status;
        
        switch (status) {
          case 'QUEUED':
            updateStep('queue');
            updateProgress(40, '任务正在排队等待处理...', 'info');
            break;
            
          case 'PROCESSING':
            updateStep('process');
            updateProgress(60, '正在进行格式转换处理...', 'info');
            break;
            
          case 'FINISH':
            updateStep('complete', 'completed');
            updateProgress(100, '转换完成！', 'success');
            
            statusText.innerHTML = `
            <div>
             转换完成！
              <a href="${data.data.result_url}" target="_blank" class="fr-download-btn">
                下载转换结果
              </a>
            </div>
             
            `;
            
            clearInterval(pollInterval);
            $('fr-convert').disabled = false;
            break;
            
          case 'FAILED':
            updateProgress(0, `转换失败: ${data.data.error || '未知错误'}`, 'error');
            clearInterval(pollInterval);
            $('fr-convert').disabled = false;
            break;
        }
      } catch (error) {
        updateProgress(0, `状态查询失败: ${error.message}`, 'error');
        clearInterval(pollInterval);
        $('fr-convert').disabled = false;
      }
    }, 2000);
  };

  // 加载格式列表
  fetch(`${API}/formats`)
    .then(response => response.json())
    .then(data => {
      formatSelect.innerHTML = '';
      (data.supported_formats || []).forEach(format => {
        const option = document.createElement('option');
        option.value = format;
        option.textContent = format.toUpperCase();
        formatSelect.appendChild(option);
      });
      
      if (DEF_TO) {
        formatSelect.value = DEF_TO;
      }
    })
    .catch(error => {
      formatSelect.innerHTML = '<option value="">格式加载失败</option>';
    });
})();
</script>

<?php get_footer(); ?>
