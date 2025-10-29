/**
 * WebView应用前端脚本
 * 处理前端交互和与Python后端的通信
 */

// 页面加载完成
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成');
    
    // 初始化配置
    loadAllConfigs();
    
    // 加载账号列表
    loadAccounts();

    // 检查pywebview是否可用
    if (typeof window.pywebview !== 'undefined') {
        window.pywebview.api.get_info().then(function(response) {
            console.log('后端信息:', response);
        }).catch(function(error) {
            console.error('获取后端信息失败:', error);
        });
    } else {
        console.warn('pywebview API 未可用');
    }
    
    // 点击模态框外部关闭模态框
    window.onclick = function(event) {
        const modal = document.getElementById('batch-add-modal');
        if (event.target === modal) {
            closeBatchAddModal();
        }
    }
});

/**
 * Tab切换功能
 * @param {Event} event - 点击事件
 * @param {string} tabId - 要切换到的Tab ID
 */
function switchTab(event, tabId) {
    // 阻止默认行为
    event.preventDefault();
    
    // 隐藏所有Tab内容
    const tabPanes = document.querySelectorAll('.tab-pane');
    tabPanes.forEach(pane => {
        pane.classList.remove('active');
    });
    
    // 移除所有Tab按钮的激活状态
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.classList.remove('active');
    });
    
    // 显示目标Tab内容
    document.getElementById(tabId).classList.add('active');
    
    // 激活点击的Tab按钮
    event.currentTarget.classList.add('active');
    
    // 如果切换到账号管理页面，刷新账号列表
    if (tabId === 'accounts') {
        loadAccounts();
    }
    
    // 如果切换到设置页面，加载配置
    if (tabId === 'settings') {
        loadAllConfigs();
    }
    
    console.log('切换到Tab:', tabId);
}

/**
 * 加载所有配置到表单
 */
function loadAllConfigs() {
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        console.warn('API 不可用，请确保在WebView中运行此应用');
        return;
    }

    // 调用后端获取所有配置
    window.pywebview.api.get_all_configs().then(function(configs) {
        // 填充设置
        if (configs.api_key !== undefined) document.getElementById('api_key').value = configs.api_key;
        if (configs.api_proxy !== undefined) document.getElementById('api_proxy').value = configs.api_proxy;
        if (configs.model !== undefined) document.getElementById('model').value = configs.model;
        if (configs.max_threads !== undefined) document.getElementById('max_threads').value = configs.max_threads;
        if (configs.daily_video_limit !== undefined) document.getElementById('daily_video_limit').value = configs.daily_video_limit;
        if (configs.daily_image_limit !== undefined) document.getElementById('daily_image_limit').value = configs.daily_image_limit;
        
        console.log('配置加载完成');
    }).catch(function(error) {
        console.error('加载配置失败:', error);
        showToast('加载配置失败: ' + error, 'error');
    });
}

/**
 * 保存设置
 */
function saveSettings() {
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        alert('API 不可用，请确保在WebView中运行此应用');
        return;
    }
    
    // 获取表单值
    const apiKey = document.getElementById('api_key').value;
    const apiProxy = document.getElementById('api_proxy').value;
    const model = document.getElementById('model').value;
    const maxThreads = document.getElementById('max_threads').value;
    const dailyVideoLimit = document.getElementById('daily_video_limit').value;
    const dailyImageLimit = document.getElementById('daily_image_limit').value;
    
    // 验证输入
    if (maxThreads < 1 || dailyVideoLimit < 1 || dailyImageLimit < 1) {
        showToast('请输入有效的数值', 'error');
        return;
    }
    
    // 保存配置
    const savePromises = [
        window.pywebview.api.set_config('api_key', apiKey),
        window.pywebview.api.set_config('api_proxy', apiProxy),
        window.pywebview.api.set_config('model', model),
        window.pywebview.api.set_config('max_threads', maxThreads),
        window.pywebview.api.set_config('daily_video_limit', dailyVideoLimit),
        window.pywebview.api.set_config('daily_image_limit', dailyImageLimit)
    ];
    
    Promise.all(savePromises)
        .then(function(results) {
            // 检查所有请求是否都成功
            const allSuccess = results.every(result => result && result.success);
            if (allSuccess) {
                showToast('设置保存成功', 'success');
                console.log('设置保存成功');
            } else {
                showToast('部分设置保存失败', 'error');
                console.error('部分设置保存失败:', results);
            }
        })
        .catch(function(error) {
            showToast('保存失败: ' + error, 'error');
            console.error('保存设置失败:', error);
        });
}

/**
 * 显示批量添加模态框
 */
function showBatchAddModal() {
    document.getElementById('batch-add-modal').style.display = 'block';
    // 清空之前的消息
    document.getElementById('modal-message').className = 'message-result';
    document.getElementById('modal-message').textContent = '';
}

/**
 * 关闭批量添加模态框
 */
function closeBatchAddModal() {
    document.getElementById('batch-add-modal').style.display = 'none';
    // 清空表单
    document.getElementById('batch_accounts').value = '';
    // 清空消息
    document.getElementById('modal-message').className = 'message-result';
    document.getElementById('modal-message').textContent = '';
}

/**
 * 批量添加账号（不设置积分）
 */
function batchAddAccounts() {
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        alert('API 不可用，请确保在WebView中运行此应用');
        return;
    }
    
    // 获取表单值
    const accountsText = document.getElementById('batch_accounts').value.trim();
    
    // 验证输入
    if (!accountsText) {
        showToast('请输入账号Token', 'error');
        return;
    }
    
    // 解析账号列表
    const tokens = accountsText.split('\n').filter(token => token.trim() !== '');
    
    if (tokens.length === 0) {
        showToast('请输入有效的账号Token', 'error');
        return;
    }
    
    // 调用后端批量添加账号（默认积分为0）
    window.pywebview.api.batch_add_accounts(tokens, 0)
        .then(function(response) {
            if (response.success) {
                showToast(`批量添加完成: 成功${response.added_count}个，失败${response.failed_count}个`, 'success');
                // 清空表单
                document.getElementById('batch_accounts').value = '';
                // 刷新账号列表
                loadAccounts();
                console.log('批量添加账号成功');
                
                // 关闭模态框
                closeBatchAddModal();
            } else {
                showToast('批量添加失败: ' + response.error, 'error');
                console.error('批量添加账号失败:', response.error);
            }
        })
        .catch(function(error) {
            showToast('批量添加失败: ' + error, 'error');
            console.error('批量添加账号异常:', error);
        });
}

/**
 * 删除选中的账号
 */
function deleteSelectedAccounts() {
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        alert('API 不可用，请确保在WebView中运行此应用');
        return;
    }
    
    // 获取选中的账号
    const checkboxes = document.querySelectorAll('#accounts-table tbody input[type="checkbox"]:checked');
    const accountIds = Array.from(checkboxes).map(checkbox => parseInt(checkbox.value));
    
    // 验证是否有选中的账号
    if (accountIds.length === 0) {
        showToast('请选择要删除的账号', 'error');
        return;
    }
    
    // 使用HTML5原生确认弹窗
    const confirmResult = confirm(`确定要删除选中的 ${accountIds.length} 个账号吗？`);
    if (!confirmResult) {
        showToast('取消删除操作', 'info');
        return;
    }
    
    // 调用后端删除账号
    window.pywebview.api.delete_accounts(accountIds)
        .then(function(response) {
            if (response.success) {
                showToast(`成功删除 ${response.deleted_count} 个账号`, 'success');
                // 刷新账号列表
                loadAccounts();
                console.log('删除账号成功');
            } else {
                showToast('删除失败: ' + response.error, 'error');
                console.error('删除账号失败:', response.error);
            }
        })
        .catch(function(error) {
            showToast('删除失败: ' + error, 'error');
            console.error('删除账号异常:', error);
        });
}

/**
 * 加载账号列表
 */
function loadAccounts() {
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        console.warn('API 不可用，请确保在WebView中运行此应用');
        return;
    }
    
    // 调用后端获取账号列表
    window.pywebview.api.get_accounts_with_usage().then(function(accounts) {
        const tableBody = document.querySelector('#accounts-table tbody');
        
        // 清空现有内容
        tableBody.innerHTML = '';
        
        if (accounts.length === 0) {
            // 如果没有账号，显示提示信息
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="6" class="no-data">暂无账号数据</td>';
            tableBody.appendChild(row);
        } else {
            // 添加每个账号到表格
            accounts.forEach(function(account) {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><input type="checkbox" value="${account.id}"></td>
                    <td>${account.id}</td>
                    <td class="token-cell">${account.token}</td>
                    <td class="points-cell">${account.points}</td>
                    <td class="count-cell">${account.image_count}</td>
                    <td class="count-cell">${account.video_count}</td>
                `;
                tableBody.appendChild(row);
            });
        }
        
        console.log('账号列表加载完成');
    }).catch(function(error) {
        console.error('加载账号列表失败:', error);
        showToast('加载账号列表失败: ' + error, 'error');
    });
}

/**
 * 全选/取消全选
 */
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('select-all');
    const checkboxes = document.querySelectorAll('#accounts-table tbody input[type="checkbox"]');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
    
    // 添加toast提示
    if (selectAllCheckbox.checked) {
        showToast('已全选所有账号', 'info');
    } else {
        showToast('已取消全选', 'info');
    }
}

/**
 * 刷新账号列表
 */
function refreshAccounts() {
    loadAccounts();
    showToast('账号列表已刷新', 'success');
}

/**
 * 显示Toast提示
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型 (success, error, 或 info)
 */
function showToast(message, type) {
    // 移除已存在的toast
    const existingToast = document.getElementById('toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    // 创建toast元素
    const toast = document.createElement('div');
    toast.id = 'toast';
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // 添加到页面
    document.body.appendChild(toast);
    
    // 显示toast
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    // 3秒后隐藏toast
    setTimeout(() => {
        toast.classList.remove('show');
        // 0.5秒后移除元素
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 500);
    }, 3000);
}

/**
 * 控制台日志辅助函数
 */
function log(message, level = 'log') {
    const timestamp = new Date().toLocaleTimeString();
    console[level](`[${timestamp}] ${message}`);
}

/**
 * 错误处理
 */
window.addEventListener('error', function(event) {
    console.error('全局错误:', event.error);
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('未处理的Promise拒绝:', event.reason);
});