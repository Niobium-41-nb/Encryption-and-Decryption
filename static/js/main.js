// 主JavaScript文件 - 文件加密解密系统

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * 初始化应用程序
 */
function initializeApp() {
    console.log('文件加密解密系统初始化完成');
    
    // 初始化工具提示
    initializeTooltips();
    
    // 初始化文件拖放功能
    initializeFileDrop();
    
    // 初始化表单验证
    initializeFormValidation();
    
    // 初始化进度条
    initializeProgressBars();
}

/**
 * 初始化Bootstrap工具提示
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * 初始化文件拖放功能
 */
function initializeFileDrop() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        const parent = input.parentElement;
        
        // 添加拖放区域样式
        if (!parent.classList.contains('file-drop-zone')) {
            parent.classList.add('file-drop-zone');
        }
        
        // 拖放事件处理
        parent.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('drag-over');
        });
        
        parent.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
        });
        
        parent.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                input.files = files;
                
                // 触发change事件
                const event = new Event('change', { bubbles: true });
                input.dispatchEvent(event);
            }
        });
    });
}

/**
 * 初始化表单验证
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                showAlert('请正确填写所有必填字段', 'warning');
            }
        });
    });
}

/**
 * 验证表单
 */
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            highlightField(field, 'error');
        } else {
            highlightField(field, 'success');
        }
    });
    
    return isValid;
}

/**
 * 高亮显示表单字段
 */
function highlightField(field, type) {
    field.classList.remove('is-valid', 'is-invalid');
    
    if (type === 'success') {
        field.classList.add('is-valid');
    } else if (type === 'error') {
        field.classList.add('is-invalid');
    }
}

/**
 * 初始化进度条
 */
function initializeProgressBars() {
    // 模拟进度条更新（实际应用中应该使用真实的上传进度）
    const progressBars = document.querySelectorAll('.progress-bar');
    
    progressBars.forEach(bar => {
        if (bar.style.width === '0%') {
            // 只在初始状态下设置动画
            setTimeout(() => {
                animateProgressBar(bar, 100, 2000);
            }, 500);
        }
    });
}

/**
 * 动画进度条
 */
function animateProgressBar(bar, target, duration) {
    const start = parseInt(bar.style.width) || 0;
    const startTime = performance.now();
    
    function updateProgress(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const currentWidth = start + (target - start) * progress;
        bar.style.width = currentWidth + '%';
        
        if (progress < 1) {
            requestAnimationFrame(updateProgress);
        }
    }
    
    requestAnimationFrame(updateProgress);
}

/**
 * 显示提示消息
 */
function showAlert(message, type = 'info') {
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // 添加到页面顶部
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    // 自动消失
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

/**
 * 文件大小格式化
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 文件类型检测
 */
function getFileType(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    const typeMap = {
        // 文档类型
        'txt': 'text',
        'pdf': 'pdf',
        'doc': 'word',
        'docx': 'word',
        'xls': 'excel',
        'xlsx': 'excel',
        
        // 图片类型
        'jpg': 'image',
        'jpeg': 'image',
        'png': 'image',
        'gif': 'image',
        
        // 压缩类型
        'zip': 'archive',
        'tar': 'archive',
        'gz': 'archive',
        'bz2': 'archive',
        
        // 媒体类型
        'mp3': 'audio',
        'mp4': 'video',
        'avi': 'video',
        'mov': 'video'
    };
    
    return typeMap[extension] || 'file';
}

/**
 * 获取文件类型图标
 */
function getFileIcon(filename) {
    const type = getFileType(filename);
    const iconMap = {
        'text': 'fa-file-text',
        'pdf': 'fa-file-pdf',
        'word': 'fa-file-word',
        'excel': 'fa-file-excel',
        'image': 'fa-file-image',
        'archive': 'fa-file-archive',
        'audio': 'fa-file-audio',
        'video': 'fa-file-video',
        'file': 'fa-file'
    };
    
    return iconMap[type] || 'fa-file';
}

/**
 * 生成随机ID
 */
function generateId(length = 8) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    
    return result;
}

/**
 * 防抖函数
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 节流函数
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

/**
 * 复制到剪贴板
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('已复制到剪贴板', 'success');
    }).catch(err => {
        console.error('复制失败:', err);
        showAlert('复制失败', 'error');
    });
}

/**
 * 下载文件
 */
function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * 加载密码本详情
 */
function loadPasswordBookDetails(bookId) {
    // 这里应该通过AJAX从服务器获取密码本详情
    // 暂时返回模拟数据
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                id: bookId,
                filename: `password_book_${bookId}.json`,
                created: new Date().toISOString(),
                rounds: 3,
                originalFile: 'example.pdf',
                metadata: {
                    encryption_time: new Date().toISOString(),
                    total_rounds: 3,
                    original_filename: 'example.pdf'
                }
            });
        }, 1000);
    });
}

/**
 * 加密强度计算
 */
function calculateEncryptionStrength(rounds, algorithms) {
    const baseStrength = rounds * 10;
    const algorithmBonus = algorithms.length * 5;
    return Math.min(baseStrength + algorithmBonus, 100);
}

/**
 * 密码强度检查
 */
function checkPasswordStrength(password) {
    if (!password) return 0;
    
    let strength = 0;
    
    // 长度检查
    if (password.length >= 8) strength += 25;
    if (password.length >= 12) strength += 15;
    
    // 字符类型检查
    if (/[a-z]/.test(password)) strength += 15;
    if (/[A-Z]/.test(password)) strength += 15;
    if (/[0-9]/.test(password)) strength += 15;
    if (/[^a-zA-Z0-9]/.test(password)) strength += 15;
    
    return Math.min(strength, 100);
}

/**
 * 获取密码强度标签
 */
function getPasswordStrengthLabel(strength) {
    if (strength < 40) return { label: '弱', class: 'danger' };
    if (strength < 70) return { label: '中等', class: 'warning' };
    if (strength < 90) return { label: '强', class: 'info' };
    return { label: '非常强', class: 'success' };
}

// 导出函数供其他脚本使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatFileSize,
        getFileType,
        getFileIcon,
        generateId,
        debounce,
        throttle,
        copyToClipboard,
        downloadFile,
        calculateEncryptionStrength,
        checkPasswordStrength,
        getPasswordStrengthLabel
    };
}