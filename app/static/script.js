/**
 * WebView应用前端脚本
 * 处理前端交互和与Python后端的通信
 */

// 页面加载完成
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成');
    
    // 加载账号列表
    loadAccounts();

    // 检查pywebview是否可用
    if (typeof window.pywebview !== 'undefined') {
        window.pywebview.api.get_info().then(function(response) {
            console.log('后端信息:', response);
            // 延时3秒确保API完全初始化后再加载主页提示词
            setTimeout(function() {
                loadHomePrompts();
            }, 3000);
        }).catch(function(error) {
            console.error('获取后端信息失败:', error);
            // 即使获取后端信息失败，也延时加载主页提示词
            setTimeout(function() {
                loadHomePrompts();
            }, 3000);
        });
    } else {
        console.warn('pywebview API 未可用');
        // API不可用时也延时加载主页提示词
        setTimeout(function() {
            loadHomePrompts();
        }, 3000);
    }
    
    // 点击模态框外部关闭模态框
    window.onclick = function(event) {
        const modal = document.getElementById('batch-add-modal');
        if (event.target === modal) {
            closeBatchAddModal();
        }
    }
    
    // 移除触摸滑动支持初始化，因为我们现在使用标准滚动条
    // initSwipeSupport();
});

/**
 * 初始化触摸滑动支持 - 注释掉整个函数
 */
/*
function initSwipeSupport() {
    // 为所有滑动区域添加触摸事件监听器
    const swipeAreas = document.querySelectorAll('.swipe-area');
    
    swipeAreas.forEach(function(area) {
        let startY = 0;
        let currentY = 0;
        
        // 触摸开始事件
        area.addEventListener('touchstart', function(e) {
            startY = e.touches[0].clientY;
        });
        
        // 触摸移动事件
        area.addEventListener('touchmove', function(e) {
            currentY = e.touches[0].clientY;
            const diffY = startY - currentY;
            
            // 滚动内容
            this.scrollTop += diffY;
            startY = currentY;
            
            // 阻止默认行为以避免页面滚动
            e.preventDefault();
        });
        
        // 触摸结束事件
        area.addEventListener('touchend', function(e) {
            // 可以在这里添加惯性滚动等高级功能
        });
    });
    
    console.log('触摸滑动支持已初始化');
}
*/

/**
 * 显示调试信息到页面
 * @param {string} message - 调试信息
 */
/*
function showDebugInfo(message) {
    const debugInfo = document.getElementById('debug-info');
    if (debugInfo) {
        debugInfo.innerHTML += message + '<br>';
        debugInfo.style.display = 'block';
    }
}
*/

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
    
    // 如果切换到主页，加载提示词
    if (tabId === 'home') {
        loadHomePrompts();
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
        console.log('从后端获取到的配置:', configs);
        // 填充设置
        if (configs.api_key !== undefined) {
            try {
                const apiKeyElement = document.getElementById('api_key');
                if (apiKeyElement) {
                    apiKeyElement.value = configs.api_key;
                    console.log('API Key已设置:', configs.api_key);
                } else {
                    console.error('无法找到API Key输入框');
                }
            } catch (e) {
                console.error('设置API Key时出错:', e);
            }
        }
        if (configs.api_proxy !== undefined) {
            try {
                const apiProxyElement = document.getElementById('api_proxy');
                if (apiProxyElement) {
                    apiProxyElement.value = configs.api_proxy;
                    console.log('API Proxy已设置:', configs.api_proxy);
                } else {
                    console.error('无法找到API Proxy输入框');
                }
            } catch (e) {
                console.error('设置API Proxy时出错:', e);
            }
        }
        if (configs.model !== undefined) {
            try {
                const modelElement = document.getElementById('model');
                if (modelElement) {
                    modelElement.value = configs.model;
                    console.log('Model已设置:', configs.model);
                } else {
                    console.error('无法找到Model输入框');
                }
            } catch (e) {
                console.error('设置Model时出错:', e);
            }
        }
        if (configs.image_prompt !== undefined) {
            try {
                const settingsPrompt = document.getElementById('settings_image_prompt');
                
                if (settingsPrompt) {
                    settingsPrompt.value = configs.image_prompt;
                    console.log('设置页面图片提示词已设置:', configs.image_prompt);
                } else {
                    console.error('无法找到设置页面图片提示词输入框');
                }
            } catch (e) {
                console.error('设置设置页面图片提示词时出错:', e);
            }
        }
        if (configs.video_prompt !== undefined) {
            try {
                const settingsVideoPrompt = document.getElementById('settings_video_prompt');
                
                if (settingsVideoPrompt) {
                    settingsVideoPrompt.value = configs.video_prompt;
                    console.log('设置页面视频提示词已设置:', configs.video_prompt);
                } else {
                    console.error('无法找到设置页面视频提示词输入框');
                }
            } catch (e) {
                console.error('设置设置页面视频提示词时出错:', e);
            }
        }
        if (configs.video_duration !== undefined) {
            try {
                // 更新单选框状态
                const videoDurationElements = document.querySelectorAll('input[name="video_duration"]');
                videoDurationElements.forEach(element => {
                    if (element.value === configs.video_duration) {
                        element.checked = true;
                    }
                });
                console.log('视频时长已设置:', configs.video_duration);
            } catch (e) {
                console.error('设置视频时长时出错:', e);
            }
        }
        // 移除视频生成方式设置
        // 移除使用国内账号开关设置
        
        console.log('配置加载完成');
    }).catch(function(error) {
        console.error('加载配置失败:', error);
        showToast('加载配置失败: ' + error, 'error');
    });
}

/**
 * 加载主页提示词
 */
function loadHomePrompts() {
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        console.warn('API 不可用，请确保在WebView中运行此应用');
        return;
    }

    // 调用后端获取提示词配置
    window.pywebview.api.get_all_configs().then(function(configs) {
        console.log('从后端获取到的提示词配置:', configs);
        // 填充主页提示词
        if (configs.image_prompt !== undefined) {
            try {
                const homePrompt = document.getElementById('home_image_prompt');
                
                if (homePrompt) {
                    homePrompt.value = configs.image_prompt;
                    console.log('首页图片提示词已设置:', configs.image_prompt);
                } else {
                    console.error('无法找到首页图片提示词输入框');
                }
            } catch (e) {
                console.error('设置首页图片提示词时出错:', e);
            }
        }
        if (configs.video_prompt !== undefined) {
            try {
                const videoPrompt = document.getElementById('video_prompt');
                
                if (videoPrompt) {
                    videoPrompt.value = configs.video_prompt;
                    console.log('首页视频提示词已设置:', configs.video_prompt);
                } else {
                    console.error('无法找到首页视频提示词输入框');
                }
            } catch (e) {
                console.error('设置首页视频提示词时出错:', e);
            }
        }
        
        console.log('主页提示词加载完成');
    }).catch(function(error) {
        console.error('加载主页提示词失败:', error);
        showToast('加载主页提示词失败: ' + error, 'error');
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
    const imagePrompt = document.getElementById('settings_image_prompt').value;
    const videoPrompt = document.getElementById('settings_video_prompt').value;
    // 获取视频时长单选框的值
    const videoDuration = document.querySelector('input[name="video_duration"]:checked').value;
    // 移除视频生成方式
    const maxThreads = document.getElementById('max_threads').value;
    const dailyVideoLimit = document.getElementById('daily_video_limit').value;
    const dailyImageLimit = document.getElementById('daily_image_limit').value;
    // 移除使用国内账号开关
    
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
        window.pywebview.api.set_config('image_prompt', imagePrompt),
        window.pywebview.api.set_config('video_prompt', videoPrompt),
        window.pywebview.api.set_config('video_duration', videoDuration),
        // 移除视频生成方式保存
        window.pywebview.api.set_config('max_threads', maxThreads),
        window.pywebview.api.set_config('daily_video_limit', dailyVideoLimit),
        window.pywebview.api.set_config('daily_image_limit', dailyImageLimit)
        // 移除使用国内账号开关保存
    ];
    
    Promise.all(savePromises)
        .then(function(results) {
            // 检查所有请求是否都成功
            const allSuccess = results.every(result => result && result.success);
            if (allSuccess) {
                showToast('设置保存成功', 'success');
                console.log('设置保存成功');
                // 同步更新首页的提示词
                document.getElementById('home_image_prompt').value = imagePrompt;
                document.getElementById('video_prompt').value = videoPrompt;
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
 * 保存图片提示词
 */
function saveImagePrompt() {
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        alert('API 不可用，请确保在WebView中运行此应用');
        return;
    }
    
    // 获取图片提示词
    const imagePrompt = document.getElementById('home_image_prompt').value;
    
    // 保存配置
    window.pywebview.api.set_config('image_prompt', imagePrompt)
        .then(function(result) {
            if (result.success) {
                showToast('图片提示词保存成功', 'success');
                console.log('图片提示词保存成功');
                // 同步更新设置页面的提示词
                document.getElementById('settings_image_prompt').value = imagePrompt;
            } else {
                showToast('图片提示词保存失败: ' + result.error, 'error');
                console.error('图片提示词保存失败:', result.error);
            }
        })
        .catch(function(error) {
            showToast('保存失败: ' + error, 'error');
            console.error('保存图片提示词失败:', error);
        });
}

/**
 * 保存视频提示词
 */
function saveVideoPrompt() {
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        alert('API 不可用，请确保在WebView中运行此应用');
        return;
    }
    
    // 获取视频提示词
    const videoPrompt = document.getElementById('video_prompt').value;
    
    // 保存配置
    window.pywebview.api.set_config('video_prompt', videoPrompt)
        .then(function(result) {
            if (result.success) {
                showToast('视频提示词保存成功', 'success');
                console.log('视频提示词保存成功');
                // 同步更新设置页面的提示词
                document.getElementById('settings_video_prompt').value = videoPrompt;
            } else {
                showToast('视频提示词保存失败: ' + result.error, 'error');
                console.error('视频提示词保存失败:', result.error);
            }
        })
        .catch(function(error) {
            showToast('保存失败: ' + error, 'error');
            console.error('保存视频提示词失败:', error);
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
        showToast('请输入账号信息', 'error');
        return;
    }
    
    // 解析账号列表
    const accountLines = accountsText.split('\n').filter(line => line.trim() !== '');
    
    if (accountLines.length === 0) {
        showToast('请输入有效的账号信息', 'error');
        return;
    }
    
    // 调用后端批量添加账号（不再传递积分参数）
    window.pywebview.api.batch_add_accounts(accountLines)
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
        // 保存账号数据
        window.allAccounts = accounts;
        
        // 渲染所有账号
        filterAccounts();
        
        console.log('账号列表加载完成');
    }).catch(function(error) {
        console.error('加载账号列表失败:', error);
        showToast('加载账号列表失败: ' + error, 'error');
    });
}

/**
 * 筛选账号
 */
function filterAccounts() {
    // 移除筛选功能，直接渲染所有账号
    renderAccountsTable(window.allAccounts || []);
}

/**
 * 渲染账号表格
 */
function renderAccountsTable(accounts) {
    const tableBody = document.querySelector('#accounts-table tbody');
    
    // 清空现有内容
    tableBody.innerHTML = '';
    
    if (accounts.length === 0) {
        // 如果没有账号，显示提示信息
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="5" class="no-data">暂无账号数据</td>';
        tableBody.appendChild(row);
    } else {
        // 添加每个账号到表格
        accounts.forEach(function(account) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><input type="checkbox" value="${account.id}"></td>
                <td>${account.id}</td>
                <td>${account.username}</td>
                <td class="count-cell">${account.image_count}</td>
                <td class="count-cell">${account.video_count}</td>
            `;
            tableBody.appendChild(row);
        });
    }
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
 * 导入文件夹
 */
function importFolder() {
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        alert('API 不可用，请确保在WebView中运行此应用');
        return;
    }
    
    console.log('开始导入文件夹');
    
    // 显示正在导入的提示
    showToast('正在导入文件夹，请稍候...', 'info');
    
    // 调用后端选择文件夹
    window.pywebview.api.select_folder().then(function(result) {
        console.log('文件夹选择结果:', result);
        if (result.success) {
            // 检查是否有文件
            if (!result.files || result.files.length === 0) {
                showToast('选择的文件夹中没有子文件夹', 'info');
                console.log('选择的文件夹中没有子文件夹');
                return;
            }
            
            console.log('成功导入文件夹，文件数量:', result.files.length);
            console.log('文件夹路径:', result.folder_path);
            
            // 直接使用虚拟滚动模式显示
            displayFolderContent(result.folder_path, result.files);
        } else {
            const errorMsg = result.error || '未知错误';
            showToast('导入文件夹失败: ' + errorMsg, 'error');
            console.error('导入文件夹失败:', errorMsg);
        }
    }).catch(function(error) {
        showToast('导入文件夹异常: ' + error, 'error');
        console.error('导入文件夹异常:', error);
    });
}

/**
 * 选择主图
 */
function selectMainImage(index) {
    // 检查全局变量是否存在
    if (!window.currentFiles || window.currentFiles.length === 0) {
        showToast('文件列表为空', 'error');
        return;
    }
    
    const file = window.currentFiles[index];
    if (!file) {
        showToast('文件不存在', 'error');
        return;
    }
    
    console.log('选择主图，文件索引:', index, '文件信息:', file);
    
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        showToast('API 不可用，请确保在WebView中运行此应用', 'error');
        return;
    }
    
    // 检查文件夹路径是否存在
    if (!file.folder_path) {
        showToast('文件夹路径不存在', 'error');
        return;
    }
    
    console.log('调用后端获取图片列表，文件夹路径:', file.folder_path);
    
    // 调用后端获取文件夹中的所有图片
    window.pywebview.api.get_images_in_folder(file.folder_path).then(function(result) {
        console.log('后端返回结果:', result);
        if (result && result.success) {
            // 检查是否有图片
            if (!result.images || result.images.length === 0) {
                showToast('该文件夹中没有图片', 'info');
                return;
            }
            showImageSelectionModal(result.images, index);
        } else {
            const errorMsg = result && result.error ? result.error : '未知错误';
            showToast('获取图片列表失败: ' + errorMsg, 'error');
        }
    }).catch(function(error) {
        console.error('获取图片列表异常:', error);
        showToast('获取图片列表异常: ' + error, 'error');
    });
}

/**
 * 显示图片选择模态框
 */
function showImageSelectionModal(images, fileIndex) {
    // 创建模态框
    const modal = document.createElement('div');
    modal.id = 'image-selection-modal';
    modal.className = 'modal';
    modal.style.display = 'block';
    
    // 创建模态框内容
    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content';
    modalContent.style.maxWidth = '90vw';  // 增加最大宽度
    modalContent.style.maxHeight = '90vh'; // 增加最大高度
    
    // 创建模态框头部
    const modalHeader = document.createElement('div');
    modalHeader.className = 'modal-header';
    modalHeader.innerHTML = `
        <h2>选择主图</h2>
        <span class="close" onclick="closeImageSelectionModal()">&times;</span>
    `;
    
    // 创建模态框主体
    const modalBody = document.createElement('div');
    modalBody.className = 'modal-body';
    modalBody.style.overflowY = 'auto';
    modalBody.style.maxHeight = 'calc(90vh - 120px)'; // 为头部和底部留出空间
    
    // 创建图片网格
    const imageGrid = document.createElement('div');
    imageGrid.style.display = 'grid';
    imageGrid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(150px, 1fr))'; // 使用自适应列数
    imageGrid.style.gap = '15px';
    imageGrid.style.padding = '10px';
    
    // 添加图片到网格
    images.forEach(function(imagePath, imgIndex) {
        const imgContainer = document.createElement('div');
        imgContainer.style.cursor = 'pointer';
        imgContainer.style.border = '2px solid transparent';
        imgContainer.style.borderRadius = '8px';
        imgContainer.style.transition = 'all 0.3s ease';
        imgContainer.style.position = 'relative';
        imgContainer.style.overflow = 'hidden';
        imgContainer.onmouseover = function() {
            imgContainer.style.borderColor = '#007bff';
            imgContainer.style.transform = 'scale(1.05)';
        };
        imgContainer.onmouseout = function() {
            imgContainer.style.borderColor = 'transparent';
            imgContainer.style.transform = 'scale(1)';
        };
        imgContainer.onclick = function() {
            setSelectedMainImage(fileIndex, imagePath);
        };
        
        // 创建图片包装容器，用于保持宽高比
        const imgWrapper = document.createElement('div');
        imgWrapper.style.width = '100%';
        imgWrapper.style.height = '0';
        imgWrapper.style.paddingBottom = '177.78%'; // 9:16 宽高比 (16/9 * 100%)
        imgWrapper.style.position = 'relative';
        imgWrapper.style.borderRadius = '4px';
        imgWrapper.style.overflow = 'hidden';
        imgWrapper.style.backgroundColor = '#f0f0f0';
        
        const img = document.createElement('img');
        img.src = `file://${imagePath}`;
        img.style.position = 'absolute';
        img.style.top = '0';
        img.style.left = '0';
        img.style.width = '100%';
        img.style.height = '100%';
        img.style.objectFit = 'contain'; // 使用contain确保图片完整显示
        img.style.objectPosition = 'center';
        img.style.backgroundColor = '#fff';
        
        imgWrapper.appendChild(img);
        imgContainer.appendChild(imgWrapper);
        imageGrid.appendChild(imgContainer);
    });
    
    modalBody.appendChild(imageGrid);
    
    // 创建模态框底部
    const modalFooter = document.createElement('div');
    modalFooter.className = 'modal-footer';
    modalFooter.innerHTML = `
        <button class="btn btn-secondary" onclick="closeImageSelectionModal()">取消</button>
    `;
    
    // 组装模态框
    modalContent.appendChild(modalHeader);
    modalContent.appendChild(modalBody);
    modalContent.appendChild(modalFooter);
    modal.appendChild(modalContent);
    
    // 添加到页面
    document.body.appendChild(modal);
    
    // 防止模态框外部点击关闭
    modal.onclick = function(event) {
        if (event.target === modal) {
            closeImageSelectionModal();
        }
    };
}

/**
 * 关闭图片选择模态框
 */
function closeImageSelectionModal() {
    const modal = document.getElementById('image-selection-modal');
    if (modal) {
        modal.remove();
    }
}

/**
 * 设置选中的主图
 */
function setSelectedMainImage(fileIndex, imagePath) {
    // 更新文件列表中的主图
    window.currentFiles[fileIndex].main_image = imagePath;
    
    // 关闭模态框
    closeImageSelectionModal();
    
    // 重新显示文件夹内容，只使用虚拟滚动模式
    displayFolderContent(window.currentFolderPath, window.currentFiles);
    
    showToast('主图已更新', 'success');
}

/**
 * 显示文件夹内容（优化版本 - 只使用标准滚动）
 */
function displayFolderContent(folderPath, files) {
    console.log('[DEBUG] displayFolderContent called with:', {folderPath, files});
    
    // 检查参数
    if (!folderPath || !files) {
        console.error('[ERROR] Missing parameters in displayFolderContent');
        showToast('显示文件夹内容时出现错误: 参数缺失', 'error');
        return;
    }
    
    const tableBody = document.querySelector('#folder-content-table tbody');
    console.log('[DEBUG] Found tableBody:', tableBody);
    
    // 检查tableBody是否存在
    if (!tableBody) {
        console.error('[ERROR] Could not find folder content table body');
        showToast('页面结构错误，无法显示文件夹内容', 'error');
        return;
    }
    
    try {
        // 清空现有内容
        tableBody.innerHTML = '';
        console.log('[DEBUG] Cleared tableBody innerHTML');
        
        if (files.length === 0) {
            // 如果没有文件，显示提示信息
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="4" class="no-data">文件夹中没有图片文件</td>';
            tableBody.appendChild(row);
            console.log('[DEBUG] No files to display, added placeholder row');
        } else {
            // 直接创建表格行，不使用虚拟滚动
            files.forEach(function(file, index) {
                // 为每个文件确保有uniqueId
                if (!file.uniqueId) {
                    file.uniqueId = generateUniqueId();
                    console.log('[DEBUG] Generated uniqueId for file at index', index, ':', file.uniqueId);
                }
                const row = createFileRow(file, index);
                tableBody.appendChild(row);
                console.log('[DEBUG] Added row for file at index:', index);
            });
            
            // 保存当前文件夹路径和文件列表到全局变量
            window.currentFolderPath = folderPath;
            window.currentFiles = files;
            
            console.log('[DEBUG] Set window.currentFiles with length:', window.currentFiles.length);
            console.log('[DEBUG] Table body children count after adding rows:', tableBody.children.length);
            showToast(`成功导入文件夹，找到 ${files.length} 个子文件夹`, 'success');
        }
    } catch (error) {
        console.error('[ERROR] Exception in displayFolderContent:', error);
        showToast('显示文件夹内容时发生错误: ' + error.message, 'error');
    }
}

/**
 * 处理滚动事件
 */
function handleScroll(event) {
    const container = event.target;
    
    // 检查必要的数据属性
    if (!container.dataset.files || !container.dataset.itemHeight || !container.dataset.visibleCount) {
        console.warn('滚动容器缺少必要的数据属性');
        return;
    }
    
    const scrollTop = container.scrollTop;
    const itemHeight = parseInt(container.dataset.itemHeight);
    const visibleCount = parseInt(container.dataset.visibleCount);
    
    // 解析文件数据
    let files;
    try {
        files = JSON.parse(container.dataset.files);
    } catch (e) {
        console.error('解析文件数据失败:', e);
        return;
    }
    
    // 计算应该显示的起始索引
    const startIndex = Math.floor(scrollTop / itemHeight);
    const endIndex = Math.min(startIndex + visibleCount, files.length);
    
    // 只有当显示范围发生变化时才重新渲染
    const currentStartIndex = parseInt(container.dataset.startIndex || '0');
    if (Math.abs(startIndex - currentStartIndex) > 5) {
        renderVisibleItems(container, files, startIndex, endIndex);
        container.dataset.startIndex = String(startIndex);
    }
}

/**
 * 处理最外层容器滚动事件（用于虚拟滚动）
 */
function handleScrollForVirtualContainer(virtualContainer, event) {
    // 检查虚拟容器是否在视口中
    const rect = virtualContainer.getBoundingClientRect();
    const isVisible = rect.top < window.innerHeight && rect.bottom > 0;
    
    if (!isVisible) {
        return;
    }
    
    // 检查必要的数据属性
    if (!virtualContainer.dataset.files || !virtualContainer.dataset.itemHeight || !virtualContainer.dataset.visibleCount) {
        console.warn('虚拟滚动容器缺少必要的数据属性');
        return;
    }
    
    // 获取最外层容器的滚动位置
    const outerContainer = document.querySelector('.tab-content');
    if (!outerContainer) {
        console.warn('无法找到最外层容器');
        return;
    }
    
    // 计算虚拟容器相对于最外层容器的位置
    const scrollTop = outerContainer.scrollTop;
    const containerOffset = virtualContainer.offsetTop;
    const relativeScrollTop = Math.max(0, scrollTop - containerOffset);
    
    const itemHeight = parseInt(virtualContainer.dataset.itemHeight);
    const visibleCount = parseInt(virtualContainer.dataset.visibleCount);
    
    // 解析文件数据
    let files;
    try {
        files = JSON.parse(virtualContainer.dataset.files);
    } catch (e) {
        console.error('解析文件数据失败:', e);
        return;
    }
    
    // 计算应该显示的起始索引
    const startIndex = Math.floor(relativeScrollTop / itemHeight);
    const endIndex = Math.min(startIndex + visibleCount, files.length);
    
    // 只有当显示范围发生变化时才重新渲染
    const currentStartIndex = parseInt(virtualContainer.dataset.startIndex || '0');
    if (Math.abs(startIndex - currentStartIndex) > 5) {
        renderVisibleItems(virtualContainer, files, startIndex, endIndex);
        virtualContainer.dataset.startIndex = String(startIndex);
    }
}

/**
 * 渲染可见项目
 */
function renderVisibleItems(container, files, startIndex, endIndex) {
    // 检查参数
    if (!container || !files) {
        console.error('渲染可见项目时参数缺失');
        return;
    }
    
    try {
        const visibleContainer = container.querySelector('div[style*="absolute"]');
        if (!visibleContainer) {
            console.warn('无法找到可视区域容器');
            return;
        }
        
        // 检查索引范围
        if (startIndex < 0 || endIndex > files.length) {
            console.warn('索引超出文件范围:', startIndex, endIndex, files.length);
            return;
        }
        
        // 清空当前可见项目
        visibleContainer.innerHTML = '';
        
        // 设置可见容器的顶部位置
        const itemHeight = parseInt(container.dataset.itemHeight) || 180;
        visibleContainer.style.top = `${startIndex * itemHeight}px`;
        
        // 渲染可见项目
        for (let i = startIndex; i < endIndex; i++) {
            if (i >= files.length) break;
            
            const file = files[i];
            if (!file) {
                console.warn('文件数据缺失，索引:', i);
                // 创建一个占位符行
                const placeholderRow = document.createElement('div');
                placeholderRow.style.display = 'table-row';
                placeholderRow.style.height = '180px';
                placeholderRow.style.width = '100%';
                placeholderRow.innerHTML = `
                    <div style="display: table-cell; padding: 10px; width: 15.4%; vertical-align: top;">
                        <div style="color: #999;">文件数据缺失</div>
                    </div>
                    <div style="display: table-cell; padding: 10px; width: 61.5%; vertical-align: top;"></div>
                    <div style="display: table-cell; padding: 10px; width: 15.4%; vertical-align: top;"></div>
                    <div style="display: table-cell; padding: 10px; width: 7.7%; vertical-align: top;"></div>
                `;
                visibleContainer.appendChild(placeholderRow);
                continue;
            }
            
            const row = createFileRow(file, i);
            visibleContainer.appendChild(row);
        }
    } catch (error) {
        console.error('渲染可见项目时发生错误:', error);
        showToast('渲染可见项目时发生错误: ' + error.message, 'error');
    }
}

/**
 * 创建文件行元素
 */
function createFileRow(file, index) {
    try {
        const row = document.createElement('div');
        row.style.display = 'table-row';
        row.style.height = '180px'; // 使用固定的默认高度
        row.style.width = '100%'; // 确保行宽度为100%
        
        // 检查必要的文件属性
        if (!file.main_image) {
            showToast('文件缺少主图信息', 'error');
            // 返回一个带有错误信息的行元素
            row.innerHTML = `
                <div style="display: table-cell; padding: 10px;" colspan="4">
                    <div style="color: red;">文件缺少主图信息</div>
                </div>
            `;
            return row;
        }
        
        // 确保文件有uniqueId
        if (!file.uniqueId) {
            file.uniqueId = generateUniqueId();
        }
        
        // 创建4个模特图坑位（待生成）
        let modelImagesHtml = '';
        for (let i = 0; i < 4; i++) {
            modelImagesHtml += `<div style="width: 120px; height: 120px; border: 3px dashed #ccc; display: inline-flex; align-items: center; justify-content: center; margin: 5px; font-size: 14px; color: #999; border-radius: 6px; aspect-ratio: 9/16;">待生成</div>`;
        }
        
        // 创建1个视频坑位（待生成）
        let videosHtml = '';
        videosHtml += `<div style="width: 120px; height: 120px; border: 3px dashed #ccc; display: inline-flex; align-items: center; justify-content: center; margin: 5px; font-size: 14px; color: #999; border-radius: 6px; aspect-ratio: 9/16;">待生成</div>`;
        
        row.innerHTML = `
            <div style="display: table-cell; padding: 10px; width: 15.4%; vertical-align: top;">
                <img src="file://${file.main_image}" alt="主图" style="width: 120px; height: 120px; object-fit: cover; cursor: pointer; border-radius: 6px;" onclick="selectMainImage(${index})">
                <div style="margin-top: 5px; font-size: 12px;"></div>
            </div>
            <div style="display: table-cell; padding: 10px; width: 61.5%; vertical-align: top;">
                <div class="generated-images" data-item-index="${index}" data-unique-id="${file.uniqueId}">
                    ${modelImagesHtml}
                </div>
            </div>
            <div style="display: table-cell; padding: 10px; width: 15.4%; vertical-align: top;">
                <div class="generated-videos">
                    ${videosHtml}
                </div>
            </div>
            <div style="display: table-cell; padding: 10px; width: 7.7%; vertical-align: top; position: relative;">
                <div class="action-buttons">
                    <button class="btn btn-small btn-primary" onclick="generateImage(${index})">图片生成</button>
                    <button class="btn btn-small btn-secondary" onclick="generateVideo(${index})">视频生成</button>
                    <button class="btn btn-small btn-danger" onclick="deleteItem(${index})">删除</button>
                </div>
                <!-- 状态指示器 -->
                <div class="status-indicator" id="status-${file.uniqueId}" style="display: none; position: absolute; top: 5px; right: 5px; width: 20px; height: 20px; border-radius: 50%; background-color: #007bff; animation: blink 1s infinite;"></div>
            </div>
        `;
        
        // 如果有uniqueId，从后端获取已生成的图片并显示
        if (file.uniqueId && typeof window.pywebview !== 'undefined' && window.pywebview.api) {
            window.pywebview.api.get_generated_images(file.uniqueId).then(function(result) {
                if (result.success && result.images && result.images.length > 0) {
                    // 找到对应的模特图容器
                    const modelImagesContainer = row.querySelector('.generated-images');
                    if (modelImagesContainer) {
                        // 更新显示已生成的图片
                        updateModelImages(modelImagesContainer, result.images, file.uniqueId);
                    }
                }
            }).catch(function(error) {
                console.error('获取已生成图片失败:', error);
            });
            
            // 从后端获取已生成的视频并显示
            window.pywebview.api.get_generated_videos(file.uniqueId).then(function(result) {
                if (result.success && result.videos && result.videos.length > 0) {
                    // 找到对应的视频容器
                    const videosContainer = row.querySelector('.generated-videos');
                    if (videosContainer) {
                        // 更新显示已生成的视频
                        updateVideo(videosContainer, result.videos, file.uniqueId);
                    }
                }
            }).catch(function(error) {
                console.error('获取已生成视频失败:', error);
            });
        }
        
        return row;
    } catch (error) {
        showToast('创建行元素时发生错误: ' + error.message, 'error');
        
        // 返回一个空的行元素
        const row = document.createElement('div');
        row.style.display = 'table-row';
        row.innerHTML = `
            <div style="display: table-cell; padding: 10px; width: 100%;" colspan="4">
                <div style="color: red;">创建行元素时发生错误: ${error.message}</div>
            </div>
        `;
        return row;
    }
}

/**
 * 滚动到指定项目
 */
function scrollToItem(index) {
    const container = document.getElementById('virtual-scroll-container');
    if (container) {
        const itemHeight = parseInt(container.dataset.itemHeight);
        const scrollTop = index * itemHeight;
        container.scrollTop = scrollTop;
    }
}

/**
 * 图片批量生成
 */
function batchGenerateImages() {
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        alert('API 不可用，请确保在WebView中运行此应用');
        return;
    }
    
    if (!window.currentFiles || window.currentFiles.length === 0) {
        showToast('请先导入文件夹', 'error');
        return;
    }
    
    const imagePrompt = document.getElementById('home_image_prompt').value;
    if (!imagePrompt) {
        showToast('请输入图片提示词', 'error');
        return;
    }
    
    // 修改所有图片生成按钮文本为"生成中..."
    const tableRows = document.querySelectorAll('#folder-content-table tbody tr');
    tableRows.forEach((row, index) => {
        const imageButton = row.querySelector('.btn-primary'); // 图片生成按钮
        if (imageButton) {
            imageButton.textContent = '图片生成中...';
            imageButton.disabled = true; // 禁用按钮防止重复点击
        }
    });
    
    // 显示所有文件的状态指示器
    window.currentFiles.forEach((file, index) => {
        if (file.uniqueId) {
            const statusIndicator = document.getElementById(`status-${file.uniqueId}`);
            if (statusIndicator) {
                statusIndicator.style.display = 'block';
                statusIndicator.style.backgroundColor = '#007bff'; // 蓝色表示正在处理
            }
        }
    });
    
    // 显示正在生成的提示
    showToast('正在批量生成图片，请稍候...', 'info');
    
    // 调用后端批量生成图片
    window.pywebview.api.batch_generate_images(window.currentFiles, imagePrompt).then(function(result) {
        // 恢复所有图片生成按钮文本
        tableRows.forEach((row, index) => {
            const imageButton = row.querySelector('.btn-primary'); // 图片生成按钮
            if (imageButton) {
                imageButton.textContent = '图片生成';
                imageButton.disabled = false; // 启用按钮
            }
        });
        
        // 隐藏所有文件的状态指示器
        window.currentFiles.forEach((file, index) => {
            if (file.uniqueId) {
                const statusIndicator = document.getElementById(`status-${file.uniqueId}`);
                if (statusIndicator) {
                    statusIndicator.style.display = 'none';
                }
            }
        });
        if (result.success) {
            showToast(`图片批量生成完成: 成功${result.success_count}个，失败${result.failed_count}个`, 'success');
            // 刷新文件夹内容显示
            // importFolder(); // 不再刷新整个文件夹，而是保留已生成的图片
        } else {
            showToast('图片批量生成失败: ' + result.error, 'error');
        }
    }).catch(function(error) {
        // 恢复所有图片生成按钮文本
        tableRows.forEach((row, index) => {
            const imageButton = row.querySelector('.btn-primary'); // 图片生成按钮
            if (imageButton) {
                imageButton.textContent = '图片生成';
                imageButton.disabled = false; // 启用按钮
            }
        });
        
        // 隐藏所有文件的状态指示器
        window.currentFiles.forEach((file, index) => {
            if (file.uniqueId) {
                const statusIndicator = document.getElementById(`status-${file.uniqueId}`);
                if (statusIndicator) {
                    statusIndicator.style.display = 'none';
                }
            }
        });
        showToast('图片批量生成异常: ' + error, 'error');
        console.error('图片批量生成异常:', error);
    });
}

/**
 * 视频批量生成
 */
function batchGenerateVideos() {
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        alert('API 不可用，请确保在WebView中运行此应用');
        return;
    }
    
    if (!window.currentFiles || window.currentFiles.length === 0) {
        showToast('请先导入文件夹', 'error');
        return;
    }
    
    const videoPrompt = document.getElementById('video_prompt').value;
    if (!videoPrompt) {
        showToast('请输入视频提示词', 'error');
        return;
    }
    
    // 修改所有视频生成按钮文本为"生成中..."
    const tableRows = document.querySelectorAll('#folder-content-table tbody tr');
    tableRows.forEach((row, index) => {
        const videoButton = row.querySelector('.btn-secondary'); // 视频生成按钮
        if (videoButton) {
            videoButton.textContent = '视频生成中...';
            videoButton.disabled = true; // 禁用按钮防止重复点击
        }
    });
    
    // 显示所有文件的状态指示器
    window.currentFiles.forEach((file, index) => {
        if (file.uniqueId) {
            const statusIndicator = document.getElementById(`status-${file.uniqueId}`);
            if (statusIndicator) {
                statusIndicator.style.display = 'block';
                statusIndicator.style.backgroundColor = '#007bff'; // 蓝色表示正在处理
            }
        }
    });
    
    // 显示正在生成的提示
    showToast('正在批量生成视频，请稍候...', 'info');
    
    // 调用后端批量生成视频
    window.pywebview.api.batch_generate_videos(window.currentFiles, videoPrompt).then(function(result) {
        // 恢复所有视频生成按钮文本
        tableRows.forEach((row, index) => {
            const videoButton = row.querySelector('.btn-secondary'); // 视频生成按钮
            if (videoButton) {
                videoButton.textContent = '视频生成';
                videoButton.disabled = false; // 启用按钮
            }
        });
        
        // 隐藏所有文件的状态指示器
        window.currentFiles.forEach((file, index) => {
            if (file.uniqueId) {
                const statusIndicator = document.getElementById(`status-${file.uniqueId}`);
                if (statusIndicator) {
                    statusIndicator.style.display = 'none';
                }
            }
        });
        if (result.success) {
            showToast(`视频批量生成完成: 成功${result.success_count}个，失败${result.failed_count}个`, 'success');
            // 刷新文件夹内容显示以更新视频
            if (window.currentFolderPath && window.currentFiles) {
                displayFolderContent(window.currentFolderPath, window.currentFiles);
            }
        } else {
            showToast('视频批量生成失败: ' + result.error, 'error');
        }
    }).catch(function(error) {
        // 恢复所有视频生成按钮文本
        tableRows.forEach((row, index) => {
            const videoButton = row.querySelector('.btn-secondary'); // 视频生成按钮
            if (videoButton) {
                videoButton.textContent = '视频生成';
                videoButton.disabled = false; // 启用按钮
            }
        });
        
        // 隐藏所有文件的状态指示器
        window.currentFiles.forEach((file, index) => {
            if (file.uniqueId) {
                const statusIndicator = document.getElementById(`status-${file.uniqueId}`);
                if (statusIndicator) {
                    statusIndicator.style.display = 'none';
                }
            }
        });
        showToast('视频批量生成异常: ' + error, 'error');
        console.error('视频批量生成异常:', error);
    });
}

/**
 * 生成视频
 */
function generateVideo(index) {
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        alert('API 不可用，请确保在WebView中运行此应用');
        return;
    }
    
    const file = window.currentFiles[index];
    if (!file) {
        showToast('文件不存在', 'error');
        return;
    }
    
    // 获取视频提示词
    const prompt = document.getElementById('video_prompt').value;
    if (!prompt) {
        showToast('请输入视频提示词', 'error');
        return;
    }
    
    // 显示状态指示器
    if (file.uniqueId) {
        const statusIndicator = document.getElementById(`status-${file.uniqueId}`);
        if (statusIndicator) {
            statusIndicator.style.display = 'block';
            statusIndicator.style.backgroundColor = '#007bff'; // 蓝色表示正在处理
        }
    }
    
    // 修改按钮文本为"生成中..."
    const tableRows = document.querySelectorAll('#folder-content-table tbody tr');
    if (tableRows.length > index) {
        const row = tableRows[index];
        const videoButton = row.querySelector('.btn-secondary'); // 视频生成按钮
        if (videoButton) {
            videoButton.textContent = '视频生成中...';
            videoButton.disabled = true; // 禁用按钮防止重复点击
        }
    }
    
    // 获取模特图中的第一张图片作为视频生成的源图片
    let imageToUse = file.main_image; // 默认使用主图
    
    // 尝试获取已生成的模特图中的第一张
    if (file.uniqueId && typeof window.pywebview !== 'undefined' && window.pywebview.api) {
        // 同步获取已生成的图片列表
        window.pywebview.api.get_generated_images(file.uniqueId).then(function(result) {
            if (result.success && result.images && result.images.length > 0) {
                // 使用第一张模特图
                imageToUse = result.images[0];
                console.log('[DEBUG] Using first model image for video generation:', imageToUse);
            } else {
                console.log('[DEBUG] No model images found, using main image for video generation:', imageToUse);
            }
            
            // 显示正在生成的提示
            showToast('正在生成视频，请稍候...', 'info');
            
            // 调用后端生成视频
            window.pywebview.api.generate_video(imageToUse, prompt).then(function(result) {
                // 隐藏状态指示器
                if (file.uniqueId) {
                    const statusIndicator = document.getElementById(`status-${file.uniqueId}`);
                    if (statusIndicator) {
                        statusIndicator.style.display = 'none';
                    }
                }
                // 恢复按钮文本
                if (tableRows.length > index) {
                    const row = tableRows[index];
                    const videoButton = row.querySelector('.btn-secondary'); // 视频生成按钮
                    if (videoButton) {
                        videoButton.textContent = '视频生成';
                        videoButton.disabled = false; // 启用按钮
                    }
                }
                
                if (result.success) {
                    showToast('视频生成成功', 'success');
                    console.log('[DEBUG] Video generation result:', result);
                    // 如果有返回的视频路径，更新视频显示
                    if (result.video_path) {
                        console.log('[DEBUG] Video path found:', result.video_path);
                        // 找到对应的视频容器
                        const allTableRows = document.querySelectorAll('#folder-content-table tbody tr');
                        console.log('[DEBUG] Table rows count:', allTableRows.length);
                        console.log('[DEBUG] Target index:', index);
                        if (allTableRows.length > index) {
                            const targetRow = allTableRows[index];
                            console.log('[DEBUG] Target row:', targetRow);
                            const videosContainer = targetRow.querySelector('.generated-videos');
                            console.log('[DEBUG] Videos container:', videosContainer);
                            if (videosContainer) {
                                // 更新显示生成的视频
                                console.log('[DEBUG] Updating video display with path:', result.video_path);
                                updateVideo(videosContainer, [result.video_path], file.uniqueId);
                            } else {
                                console.error('[ERROR] Videos container not found');
                            }
                        } else {
                            console.error('[ERROR] Table rows not enough, length:', allTableRows.length, 'index:', index);
                        }
                    } else {
                        console.log('[DEBUG] No video path in result');
                    }
                } else {
                    showToast('视频生成失败: ' + result.error, 'error');
                }
            }).catch(function(error) {
                // 隐藏状态指示器
                if (file.uniqueId) {
                    const statusIndicator = document.getElementById(`status-${file.uniqueId}`);
                    if (statusIndicator) {
                        statusIndicator.style.display = 'none';
                    }
                }
                // 恢复按钮文本
                if (tableRows.length > index) {
                    const row = tableRows[index];
                    const videoButton = row.querySelector('.btn-secondary'); // 视频生成按钮
                    if (videoButton) {
                        videoButton.textContent = '视频生成';
                        videoButton.disabled = false; // 启用按钮
                    }
                }
                
                showToast('视频生成异常: ' + error, 'error');
                console.error('视频生成异常:', error);
            });
        }).catch(function(error) {
            console.error('获取已生成图片失败，使用主图生成视频:', error);
            // 如果获取失败，仍然使用主图生成视频
            showToast('正在生成视频，请稍候...', 'info');
            
            // 调用后端生成视频
            window.pywebview.api.generate_video(imageToUse, prompt).then(function(result) {
                // 隐藏状态指示器
                if (file.uniqueId) {
                    const statusIndicator = document.getElementById(`status-${file.uniqueId}`);
                    if (statusIndicator) {
                        statusIndicator.style.display = 'none';
                    }
                }
                // 恢复按钮文本
                if (tableRows.length > index) {
                    const row = tableRows[index];
                    const videoButton = row.querySelector('.btn-secondary'); // 视频生成按钮
                    if (videoButton) {
                        videoButton.textContent = '视频生成';
                        videoButton.disabled = false; // 启用按钮
                    }
                }
                
                if (result.success) {
                    showToast('视频生成成功', 'success');
                    console.log('[DEBUG] Video generation result:', result);
                    // 如果有返回的视频路径，更新视频显示
                    if (result.video_path) {
                        console.log('[DEBUG] Video path found:', result.video_path);
                        // 找到对应的视频容器
                        const allTableRows = document.querySelectorAll('#folder-content-table tbody tr');
                        console.log('[DEBUG] Table rows count:', allTableRows.length);
                        console.log('[DEBUG] Target index:', index);
                        if (allTableRows.length > index) {
                            const targetRow = allTableRows[index];
                            console.log('[DEBUG] Target row:', targetRow);
                            const videosContainer = targetRow.querySelector('.generated-videos');
                            console.log('[DEBUG] Videos container:', videosContainer);
                            if (videosContainer) {
                                // 更新显示生成的视频
                                console.log('[DEBUG] Updating video display with path:', result.video_path);
                                updateVideo(videosContainer, [result.video_path], file.uniqueId);
                            } else {
                                console.error('[ERROR] Videos container not found');
                            }
                        } else {
                            console.error('[ERROR] Table rows not enough, length:', allTableRows.length, 'index:', index);
                        }
                    } else {
                        console.log('[DEBUG] No video path in result');
                    }
                } else {
                    showToast('视频生成失败: ' + result.error, 'error');
                }
            }).catch(function(error) {
                // 隐藏状态指示器
                if (file.uniqueId) {
                    const statusIndicator = document.getElementById(`status-${file.uniqueId}`);
                    if (statusIndicator) {
                        statusIndicator.style.display = 'none';
                    }
                }
                // 恢复按钮文本
                if (tableRows.length > index) {
                    const row = tableRows[index];
                    const videoButton = row.querySelector('.btn-secondary'); // 视频生成按钮
                    if (videoButton) {
                        videoButton.textContent = '视频生成';
                        videoButton.disabled = false; // 启用按钮
                    }
                }
                
                showToast('视频生成异常: ' + error, 'error');
                console.error('视频生成异常:', error);
            });
        });
    } else {
        // 如果无法获取uniqueId或API不可用，直接使用主图生成视频
        console.log('[DEBUG] API not available or no uniqueId, using main image for video generation:', imageToUse);
        showToast('正在生成视频，请稍候...', 'info');
        
        // 调用后端生成视频
        window.pywebview.api.generate_video(imageToUse, prompt).then(function(result) {
            // 隐藏状态指示器
            if (file.uniqueId) {
                const statusIndicator = document.getElementById(`status-${file.uniqueId}`);
                if (statusIndicator) {
                    statusIndicator.style.display = 'none';
                }
            }
            // 恢复按钮文本
            if (tableRows.length > index) {
                const row = tableRows[index];
                const videoButton = row.querySelector('.btn-secondary'); // 视频生成按钮
                if (videoButton) {
                    videoButton.textContent = '视频生成';
                    videoButton.disabled = false; // 启用按钮
                }
            }
            
            if (result.success) {
                showToast('视频生成成功', 'success');
                console.log('[DEBUG] Video generation result:', result);
                // 如果有返回的视频路径，更新视频显示
                if (result.video_path) {
                    console.log('[DEBUG] Video path found:', result.video_path);
                    // 找到对应的视频容器
                    const allTableRows = document.querySelectorAll('#folder-content-table tbody tr');
                    console.log('[DEBUG] Table rows count:', allTableRows.length);
                    console.log('[DEBUG] Target index:', index);
                    if (allTableRows.length > index) {
                        const targetRow = allTableRows[index];
                        console.log('[DEBUG] Target row:', targetRow);
                        const videosContainer = targetRow.querySelector('.generated-videos');
                        console.log('[DEBUG] Videos container:', videosContainer);
                        if (videosContainer) {
                            // 更新显示生成的视频
                            console.log('[DEBUG] Updating video display with path:', result.video_path);
                            updateVideo(videosContainer, [result.video_path], file.uniqueId);
                        } else {
                            console.error('[ERROR] Videos container not found');
                        }
                    } else {
                        console.error('[ERROR] Table rows not enough, length:', allTableRows.length, 'index:', index);
                    }
                } else {
                    console.log('[DEBUG] No video path in result');
                }
            } else {
                showToast('视频生成失败: ' + result.error, 'error');
            }
        }).catch(function(error) {
            // 隐藏状态指示器
            if (file.uniqueId) {
                const statusIndicator = document.getElementById(`status-${file.uniqueId}`);
                if (statusIndicator) {
                    statusIndicator.style.display = 'none';
                }
            }
            // 恢复按钮文本
            if (tableRows.length > index) {
                const row = tableRows[index];
                const videoButton = row.querySelector('.btn-secondary'); // 视频生成按钮
                if (videoButton) {
                    videoButton.textContent = '视频生成';
                    videoButton.disabled = false; // 启用按钮
                }
            }
            
            showToast('视频生成异常: ' + error, 'error');
            console.error('视频生成异常:', error);
        });
    }
}

/**
 * 生成图片
 */
function generateImage(index) {
    console.log('[DEBUG] generateImage called with index:', index);
    console.log('[DEBUG] window.currentFiles:', window.currentFiles);
    
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        alert('API 不可用，请确保在WebView中运行此应用');
        return;
    }
    
    // 验证索引有效性
    if (!window.currentFiles) {
        console.error('[ERROR] window.currentFiles is null or undefined');
        showToast('文件列表未初始化', 'error');
        return;
    }
    
    if (index < 0 || index >= window.currentFiles.length) {
        console.error('[ERROR] Index out of range:', index, 'Length:', window.currentFiles.length);
        showToast('文件索引超出范围', 'error');
        return;
    }
    
    const file = window.currentFiles[index];
    console.log('[DEBUG] File at index:', file);
    
    if (!file) {
        console.error('[ERROR] File is null at index:', index);
        showToast('文件不存在', 'error');
        return;
    }
    
    // 获取图片提示词
    const prompt = document.getElementById('home_image_prompt').value;
    if (!prompt) {
        showToast('请输入图片提示词', 'error');
        return;
    }
    
    // 显示状态指示器
    if (file.uniqueId) {
        const statusIndicator = document.getElementById(`status-${file.uniqueId}`);
        if (statusIndicator) {
            statusIndicator.style.display = 'block';
            statusIndicator.style.backgroundColor = '#007bff'; // 蓝色表示正在处理
        }
    }
    
    // 修改按钮文本为"生成中..."
    const tableRows = document.querySelectorAll('#folder-content-table tbody tr');
    if (tableRows.length > index) {
        const row = tableRows[index];
        const imageButton = row.querySelector('.btn-primary'); // 图片生成按钮
        if (imageButton) {
            imageButton.textContent = '图片生成中...';
            imageButton.disabled = true; // 禁用按钮防止重复点击
        }
    }
    
    // 显示正在生成的提示
    showToast('正在生成模特图，请稍候...', 'info');
    
    // 保存当前正在生成图片的item索引到全局变量（作为备用方案）
    window.currentGeneratingIndex = index;
    console.log('[DEBUG] Set currentGeneratingIndex to:', index);
    
    // 为当前文件生成一个唯一标识符，用于后续验证
    if (!file.uniqueId) {
        file.uniqueId = generateUniqueId();
        console.log('[DEBUG] Generated uniqueId for file:', file.uniqueId);
    }
    
    // 调用后端生成图片（使用图生图方式），并将index和uniqueId作为参数传递
    console.log('[DEBUG] Calling backend generate_image_with_id with index:', index, 'uniqueId:', file.uniqueId);
    window.pywebview.api.generate_image_with_id(file.main_image, index, file.uniqueId, prompt).then(function(result) {
        console.log('[DEBUG] Backend response:', result);
        // 隐藏状态指示器
        if (file.uniqueId) {
            const statusIndicator = document.getElementById(`status-${file.uniqueId}`);
            if (statusIndicator) {
                statusIndicator.style.display = 'none';
            }
        }
        // 恢复按钮文本
        if (tableRows.length > index) {
            const row = tableRows[index];
            const imageButton = row.querySelector('.btn-primary'); // 图片生成按钮
            if (imageButton) {
                imageButton.textContent = '图片生成';
                imageButton.disabled = false; // 启用按钮
            }
        }
        if (result.success) {
            showToast(result.message || '模特图生成任务已启动', 'success');
        } else {
            showToast('模特图生成失败: ' + result.error, 'error');
        }
    }).catch(function(error) {
        // 隐藏状态指示器
        if (file.uniqueId) {
            const statusIndicator = document.getElementById(`status-${file.uniqueId}`);
            if (statusIndicator) {
                statusIndicator.style.display = 'none';
            }
        }
        // 恢复按钮文本
        if (tableRows.length > index) {
            const row = tableRows[index];
            const imageButton = row.querySelector('.btn-primary'); // 图片生成按钮
            if (imageButton) {
                imageButton.textContent = '图片生成';
                imageButton.disabled = false; // 启用按钮
            }
        }
        showToast('模特图生成异常: ' + error, 'error');
        console.error('模特图生成异常:', error);
    });
}

/**
 * 生成唯一标识符
 */
function generateUniqueId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

/**
 * 处理生成的图片路径并显示在对应的item中
 * @param {Array} imagePaths - 本地图片路径或URL数组
 * @param {number} index - 项目索引
 * @param {string} uniqueId - 项目的唯一标识符
 */
function handleGeneratedImagesForItem(imagePaths, index, uniqueId) {
    // 显示成功提示
    showToast(`成功生成 ${imagePaths.length} 张模特图`, 'success');
    
    console.log('[DEBUG] handleGeneratedImagesForItem called with:', {imagePaths, index, uniqueId});
    
    // 如果提供了uniqueId，优先使用它来查找正确的项目
    let actualIndex = index;
    if (uniqueId && window.currentFiles) {
        // 通过uniqueId查找正确的索引
        actualIndex = window.currentFiles.findIndex(file => file.uniqueId === uniqueId);
        console.log('[DEBUG] Found actualIndex by uniqueId:', actualIndex);
        if (actualIndex === -1) {
            // 如果通过uniqueId找不到，回退到传递的索引
            actualIndex = index;
            console.log('[DEBUG] Falling back to passed index:', actualIndex);
        }
    }
    
    // 验证索引有效性
    if (actualIndex === undefined) {
        showToast('无法确定图片应该显示在哪个位置', 'error');
        return;
    }
    
    // 检查window.currentFiles是否存在且索引有效
    if (!window.currentFiles) {
        showToast('文件列表未初始化', 'error');
        return;
    }
    
    if (actualIndex < 0 || actualIndex >= window.currentFiles.length) {
        showToast('item索引超出范围', 'error');
        return;
    }
    
    // 确保当前文件有uniqueId
    if (!window.currentFiles[actualIndex].uniqueId) {
        window.currentFiles[actualIndex].uniqueId = uniqueId;
    }
    
    // 显示成功状态指示器（短暂显示后隐藏）
    if (uniqueId) {
        const statusIndicator = document.getElementById(`status-${uniqueId}`);
        if (statusIndicator) {
            statusIndicator.style.display = 'block';
            statusIndicator.style.backgroundColor = '#28a745'; // 绿色表示成功
            // 2秒后隐藏状态指示器
            setTimeout(() => {
                statusIndicator.style.display = 'none';
            }, 2000);
        }
    }
    
    // 直接查找对应的模特图容器（不再使用虚拟滚动）
    const tableRows = document.querySelectorAll('#folder-content-table tbody tr');
    console.log('[DEBUG] Found table rows:', tableRows.length);
    
    // 如果表格行数为0，尝试重新渲染表格
    if (tableRows.length === 0) {
        if (window.currentFolderPath && window.currentFiles) {
            displayFolderContent(window.currentFolderPath, window.currentFiles);
            // 给一点时间让DOM更新
            setTimeout(() => {
                const newTableRows = document.querySelectorAll('#folder-content-table tbody tr');
                console.log('[DEBUG] Found new table rows after re-render:', newTableRows.length);
                
                // 检查表格body的状态
                const tableBody = document.querySelector('#folder-content-table tbody');
                
                if (newTableRows.length > actualIndex) {
                    const row = newTableRows[actualIndex];
                    const modelImagesContainer = row.querySelector('.generated-images');
                    if (modelImagesContainer) {
                        console.log('[DEBUG] Calling updateModelImages with container and imagePaths');
                        updateModelImages(modelImagesContainer, imagePaths, uniqueId);
                    } else {
                        showToast('无法找到模特图容器', 'error');
                    }
                } else {
                    // 尝试直接通过tableBody查找
                    if (tableBody && tableBody.children.length > actualIndex) {
                        const row = tableBody.children[actualIndex];
                        const modelImagesContainer = row.querySelector('.generated-images');
                        if (modelImagesContainer) {
                            console.log('[DEBUG] Calling updateModelImages with container and imagePaths');
                            updateModelImages(modelImagesContainer, imagePaths, uniqueId);
                        } else {
                            showToast('无法找到模特图容器', 'error');
                        }
                    } else {
                        showToast('item索引超出范围', 'error');
                    }
                }
            }, 100);
            return;
        } else {
            showToast('无法重新显示文件夹内容', 'error');
            return;
        }
    }
    
    // 再次验证表格行数与索引的匹配性
    if (actualIndex >= tableRows.length) {
        showToast('item索引超出范围', 'error');
        return;
    }
    
    const row = tableRows[actualIndex];
    console.log('[DEBUG] Found row for index:', actualIndex, row);
    
    if (!row) {
        showToast('无法找到表格行', 'error');
        return;
    }
    
    const modelImagesContainer = row.querySelector('.generated-images');
    console.log('[DEBUG] Found modelImagesContainer:', modelImagesContainer);
    
    if (!modelImagesContainer) {
        showToast('无法找到模特图容器', 'error');
        return;
    }
    
    console.log('[DEBUG] Calling updateModelImages with container and imagePaths');
    updateModelImages(modelImagesContainer, imagePaths, uniqueId);
}

/**
 * 更新模特图显示
 */
function updateModelImages(container, imagePaths, uniqueId) {
    console.log('[DEBUG] updateModelImages called with:', {container, imagePaths, uniqueId});
    
    // 限制最多只显示4张图片
    const displayImages = imagePaths.slice(0, 4);
    
    // 为每张新图片创建显示元素
    displayImages.forEach((path, i) => {
        console.log('[DEBUG] Processing image path:', path, 'index:', i);
        
        // 检查是否已经存在相同路径的图片，避免重复添加
        const existingImages = container.querySelectorAll('img');
        let imageExists = false;
        for (let img of existingImages) {
            if (img.src === `file://${path}` || img.src === path) {
                imageExists = true;
                break;
            }
        }
        
        if (imageExists) {
            console.log('[DEBUG] Image already exists, skipping:', path);
            return; // 跳过已存在的图片
        }
        
        // 创建新的图片容器
        const imgContainer = document.createElement('div');
        imgContainer.style.display = 'inline-block';
        imgContainer.style.margin = '5px';
        imgContainer.style.position = 'relative';
        imgContainer.style.border = '3px solid transparent';
        imgContainer.style.borderRadius = '8px';
        imgContainer.style.transition = 'all 0.3s ease';
        imgContainer.style.width = '120px';
        imgContainer.style.height = '120px';
        
        // 创建图片元素
        const img = document.createElement('img');
        // 检查路径是本地路径还是URL
        if (path.startsWith('/') || path.includes('\\') || path.startsWith('file://')) {
            // 本地路径
            img.src = `file://${path}`;
        } else {
            // URL
            img.src = path;
        }
        img.alt = `模特图 ${i + 1}`;
        img.style.width = '120px';
        img.style.height = '120px';
        img.style.objectFit = 'cover';
        img.style.borderRadius = '6px';
        img.style.cursor = 'pointer';
        img.style.transition = 'all 0.3s ease';
        img.style.aspectRatio = '9/16'; // 设置图片比例为9:16
        
        // 添加单击事件，用于选择图片
        img.onclick = function() {
            // 移除其他图片的选中状态
            const allContainers = container.querySelectorAll('div[style*="inline-block"]:not([style*="dashed"])');
            allContainers.forEach(container => {
                container.style.border = '3px solid transparent';
                container.style.boxShadow = 'none';
                container.style.backgroundColor = 'transparent';
            });
            
            // 设置当前图片为选中状态
            imgContainer.style.border = '3px solid #007bff';
            imgContainer.style.boxShadow = '0 0 15px rgba(0, 123, 255, 0.9)';
            imgContainer.style.backgroundColor = 'rgba(0, 123, 255, 0.2)';
            imgContainer.style.transform = 'scale(1.05)';
        };
        
        // 添加双击事件，用于放大查看图片
        img.ondblclick = function() {
            // 创建模态框用于放大查看
            const modal = document.createElement('div');
            modal.style.position = 'fixed';
            modal.style.top = '0';
            modal.style.left = '0';
            modal.style.width = '100%';
            modal.style.height = '100%';
            modal.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
            modal.style.display = 'flex';
            modal.style.justifyContent = 'center';
            modal.style.alignItems = 'center';
            modal.style.zIndex = '10000';
            modal.style.cursor = 'pointer';
            
            const largeImg = document.createElement('img');
            // 检查路径是本地路径还是URL
            if (path.startsWith('/') || path.includes('\\') || path.startsWith('file://')) {
                // 本地路径
                largeImg.src = `file://${path}`;
            } else {
                // URL
                largeImg.src = path;
            }
            largeImg.style.maxWidth = '90%';
            largeImg.style.maxHeight = '90%';
            largeImg.style.borderRadius = '8px';
            largeImg.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.5)';
            
            // 设置图片比例为9:16
            largeImg.style.objectFit = 'contain';
            largeImg.style.aspectRatio = '9/16';
            
            modal.appendChild(largeImg);
            document.body.appendChild(modal);
            
            // 点击模态框或按ESC键关闭
            modal.onclick = function() {
                document.body.removeChild(modal);
            };
            
            // 按ESC键关闭
            const closeOnEsc = function(event) {
                if (event.key === 'Escape') {
                    document.body.removeChild(modal);
                    document.removeEventListener('keydown', closeOnEsc);
                }
            };
            document.addEventListener('keydown', closeOnEsc);
        };
        
        // 鼠标悬停效果
        img.onmouseover = function() {
            img.style.transform = 'scale(1.1)';
            imgContainer.style.boxShadow = '0 0 10px rgba(0, 123, 255, 0.6)';
        };
        
        img.onmouseout = function() {
            // 只有在未选中的情况下才恢复原始状态
            if (imgContainer.style.border.indexOf('transparent') !== -1) {
                img.style.transform = 'scale(1)';
                imgContainer.style.boxShadow = 'none';
            }
        };
        
        // 组装元素
        imgContainer.appendChild(img);
        
        // 添加到容器末尾（在占位符之前）
        const placeholders = container.querySelectorAll('div[style*="dashed"]');
        if (placeholders.length > 0) {
            // 在第一个占位符之前插入
            container.insertBefore(imgContainer, placeholders[0]);
        } else {
            // 如果没有占位符，直接添加到容器末尾
            container.appendChild(imgContainer);
        }
    });
    
    // 检查当前已有的图片数量
    const allImages = container.querySelectorAll('div[style*="inline-block"]:not([style*="dashed"])');
    
    // 如果已经有图片了，移除所有占位符
    if (allImages.length > 0) {
        const placeholders = container.querySelectorAll('div[style*="dashed"]');
        placeholders.forEach(placeholder => {
            if (placeholder.parentNode) {
                placeholder.parentNode.removeChild(placeholder);
            }
        });
    }
    
    // 确保总共只显示4个元素（图片）
    const currentImages = container.querySelectorAll('div[style*="inline-block"]:not([style*="dashed"])');
    if (currentImages.length > 4) {
        // 移除多余的图片（从末尾开始移除）
        for (let i = currentImages.length - 1; i >= 4; i--) {
            if (currentImages[i] && currentImages[i].parentNode) {
                currentImages[i].parentNode.removeChild(currentImages[i]);
            }
        }
    }
    
    // 如果当前图片少于4张，添加占位符直到4个（如果还没有占位符）
    const currentImageCount = container.querySelectorAll('div[style*="inline-block"]:not([style*="dashed"])').length;
    const placeholders = container.querySelectorAll('div[style*="dashed"]');
    
    if (currentImageCount < 4 && placeholders.length === 0) {
        // 计算需要添加的占位符数量
        const placeholdersNeeded = 4 - currentImageCount;
        for (let i = 0; i < placeholdersNeeded; i++) {
            const placeholder = document.createElement('div');
            placeholder.style.width = '120px';
            placeholder.style.height = '120px';
            placeholder.style.border = '3px dashed #ccc';
            placeholder.style.display = 'inline-flex';
            placeholder.style.alignItems = 'center';
            placeholder.style.justifyContent = 'center';
            placeholder.style.margin = '5px';
            placeholder.style.fontSize = '14px';
            placeholder.style.color = '#999';
            placeholder.style.borderRadius = '6px';
            placeholder.style.aspectRatio = '9/16';
            placeholder.textContent = '待生成';
            container.appendChild(placeholder);
        }
    }
}

/**
 * 更新视频显示
 */
function updateVideo(container, videoPaths, uniqueId) {
    console.log('[DEBUG] updateVideo called with:', {container, videoPaths, uniqueId});
    
    // 清空容器内容
    container.innerHTML = '';
    
    // 如果有视频路径，显示视频
    if (videoPaths && videoPaths.length > 0) {
        videoPaths.forEach((path, i) => {
            // 创建视频容器
            const videoContainer = document.createElement('div');
            videoContainer.style.display = 'inline-block';
            videoContainer.style.margin = '5px';
            videoContainer.style.position = 'relative';
            videoContainer.style.border = '3px solid transparent';
            videoContainer.style.borderRadius = '8px';
            videoContainer.style.transition = 'all 0.3s ease';
            videoContainer.style.width = '120px';
            videoContainer.style.height = '120px';
            
            // 创建视频缩略图元素
            const videoThumb = document.createElement('div');
            videoThumb.style.width = '120px';
            videoThumb.style.height = '120px';
            videoThumb.style.display = 'flex';
            videoThumb.style.alignItems = 'center';
            videoThumb.style.justifyContent = 'center';
            videoThumb.style.backgroundColor = '#f0f0f0';
            videoThumb.style.borderRadius = '6px';
            videoThumb.style.cursor = 'pointer';
            videoThumb.style.position = 'relative';
            videoThumb.style.aspectRatio = '9/16';
            
            // 添加播放图标
            const playIcon = document.createElement('div');
            playIcon.innerHTML = '▶';
            playIcon.style.fontSize = '24px';
            playIcon.style.color = '#007bff';
            videoThumb.appendChild(playIcon);
            
            // 添加视频标签
            const videoLabel = document.createElement('div');
            videoLabel.textContent = '视频';
            videoLabel.style.position = 'absolute';
            videoLabel.style.bottom = '5px';
            videoLabel.style.left = '5px';
            videoLabel.style.right = '5px';
            videoLabel.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
            videoLabel.style.color = 'white';
            videoLabel.style.fontSize = '12px';
            videoLabel.style.textAlign = 'center';
            videoLabel.style.padding = '2px';
            videoLabel.style.borderRadius = '3px';
            videoThumb.appendChild(videoLabel);
            
            // 添加点击事件，用于播放视频
            videoThumb.onclick = function() {
                // 调用系统默认播放器播放视频
                playVideoWithSystemPlayer(path);
            };
            
            // 鼠标悬停效果
            videoThumb.onmouseover = function() {
                videoContainer.style.boxShadow = '0 0 10px rgba(0, 123, 255, 0.6)';
            };
            
            videoThumb.onmouseout = function() {
                videoContainer.style.boxShadow = 'none';
            };
            
            // 组装元素
            videoContainer.appendChild(videoThumb);
            container.appendChild(videoContainer);
        });
    } else {
        // 如果没有视频，显示占位符
        const placeholder = document.createElement('div');
        placeholder.style.width = '120px';
        placeholder.style.height = '120px';
        placeholder.style.border = '3px dashed #ccc';
        placeholder.style.display = 'inline-flex';
        placeholder.style.alignItems = 'center';
        placeholder.style.justifyContent = 'center';
        placeholder.style.margin = '5px';
        placeholder.style.fontSize = '14px';
        placeholder.style.color = '#999';
        placeholder.style.borderRadius = '6px';
        placeholder.style.aspectRatio = '9/16';
        placeholder.textContent = '待生成';
        container.appendChild(placeholder);
    }
}

/**
 * 使用系统默认播放器播放视频
 */
function playVideoWithSystemPlayer(videoPath) {
    console.log('[DEBUG] playVideoWithSystemPlayer called with:', videoPath);
    
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        alert('API 不可用，请确保在WebView中运行此应用');
        return;
    }
    
    // 调用后端播放视频
    window.pywebview.api.play_video(videoPath).then(function(result) {
        if (!result.success) {
            showToast('播放视频失败: ' + result.error, 'error');
        }
    }).catch(function(error) {
        showToast('播放视频异常: ' + error, 'error');
        console.error('播放视频异常:', error);
    });
}

/**
 * 显示文件夹内容（优化版本 - 只使用标准滚动）
 */
function displayFolderContent(folderPath, files) {
    console.log('[DEBUG] displayFolderContent called with:', {folderPath, files});
    
    // 检查参数
    if (!folderPath || !files) {
        console.error('[ERROR] Missing parameters in displayFolderContent');
        showToast('显示文件夹内容时出现错误: 参数缺失', 'error');
        return;
    }
    
    const tableBody = document.querySelector('#folder-content-table tbody');
    console.log('[DEBUG] Found tableBody:', tableBody);
    
    // 检查tableBody是否存在
    if (!tableBody) {
        console.error('[ERROR] Could not find folder content table body');
        showToast('页面结构错误，无法显示文件夹内容', 'error');
        return;
    }
    
    try {
        // 清空现有内容
        tableBody.innerHTML = '';
        console.log('[DEBUG] Cleared tableBody innerHTML');
        
        if (files.length === 0) {
            // 如果没有文件，显示提示信息
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="4" class="no-data">文件夹中没有图片文件</td>';
            tableBody.appendChild(row);
            console.log('[DEBUG] No files to display, added placeholder row');
        } else {
            // 直接创建表格行，不使用虚拟滚动
            files.forEach(function(file, index) {
                // 为每个文件确保有uniqueId
                if (!file.uniqueId) {
                    file.uniqueId = generateUniqueId();
                    console.log('[DEBUG] Generated uniqueId for file at index', index, ':', file.uniqueId);
                }
                const row = createFileRow(file, index);
                tableBody.appendChild(row);
                console.log('[DEBUG] Added row for file at index:', index);
            });
            
            // 保存当前文件夹路径和文件列表到全局变量
            window.currentFolderPath = folderPath;
            window.currentFiles = files;
            
            console.log('[DEBUG] Set window.currentFiles with length:', window.currentFiles.length);
            console.log('[DEBUG] Table body children count after adding rows:', tableBody.children.length);
            showToast(`成功导入文件夹，找到 ${files.length} 个子文件夹`, 'success');
        }
    } catch (error) {
        console.error('[ERROR] Exception in displayFolderContent:', error);
        showToast('显示文件夹内容时发生错误: ' + error.message, 'error');
    }
}

/**
 * 创建文件行元素
 */
function createFileRow(file, index) {
    try {
        const row = document.createElement('div');
        row.style.display = 'table-row';
        row.style.height = '180px'; // 使用固定的默认高度
        row.style.width = '100%'; // 确保行宽度为100%
        
        // 检查必要的文件属性
        if (!file.main_image) {
            showToast('文件缺少主图信息', 'error');
            // 返回一个带有错误信息的行元素
            row.innerHTML = `
                <div style="display: table-cell; padding: 10px;" colspan="4">
                    <div style="color: red;">文件缺少主图信息</div>
                </div>
            `;
            return row;
        }
        
        // 确保文件有uniqueId
        if (!file.uniqueId) {
            file.uniqueId = generateUniqueId();
        }
        
        // 创建4个模特图坑位（待生成）
        let modelImagesHtml = '';
        for (let i = 0; i < 4; i++) {
            modelImagesHtml += `<div style="width: 120px; height: 120px; border: 3px dashed #ccc; display: inline-flex; align-items: center; justify-content: center; margin: 5px; font-size: 14px; color: #999; border-radius: 6px; aspect-ratio: 9/16;">待生成</div>`;
        }
        
        // 创建1个视频坑位（待生成）
        let videosHtml = '';
        videosHtml += `<div style="width: 120px; height: 120px; border: 3px dashed #ccc; display: inline-flex; align-items: center; justify-content: center; margin: 5px; font-size: 14px; color: #999; border-radius: 6px; aspect-ratio: 9/16;">待生成</div>`;
        
        row.innerHTML = `
            <div style="display: table-cell; padding: 10px; width: 15.4%; vertical-align: top;">
                <img src="file://${file.main_image}" alt="主图" style="width: 120px; height: 120px; object-fit: cover; cursor: pointer; border-radius: 6px;" onclick="selectMainImage(${index})">
                <div style="margin-top: 5px; font-size: 12px;"></div>
            </div>
            <div style="display: table-cell; padding: 10px; width: 61.5%; vertical-align: top;">
                <div class="generated-images" data-item-index="${index}" data-unique-id="${file.uniqueId}">
                    ${modelImagesHtml}
                </div>
            </div>
            <div style="display: table-cell; padding: 10px; width: 15.4%; vertical-align: top;">
                <div class="generated-videos">
                    ${videosHtml}
                </div>
            </div>
            <div style="display: table-cell; padding: 10px; width: 7.7%; vertical-align: top; position: relative;">
                <div class="action-buttons">
                    <button class="btn btn-small btn-primary" onclick="generateImage(${index})">图片生成</button>
                    <button class="btn btn-small btn-secondary" onclick="generateVideo(${index})">视频生成</button>
                    <button class="btn btn-small btn-danger" onclick="deleteItem(${index})">删除</button>
                </div>
                <!-- 状态指示器 -->
                <div class="status-indicator" id="status-${file.uniqueId}" style="display: none; position: absolute; top: 5px; right: 5px; width: 20px; height: 20px; border-radius: 50%; background-color: #007bff; animation: blink 1s infinite;"></div>
            </div>
        `;
        
        // 如果有uniqueId，从后端获取已生成的图片并显示
        if (file.uniqueId && typeof window.pywebview !== 'undefined' && window.pywebview.api) {
            window.pywebview.api.get_generated_images(file.uniqueId).then(function(result) {
                if (result.success && result.images && result.images.length > 0) {
                    // 找到对应的模特图容器
                    const modelImagesContainer = row.querySelector('.generated-images');
                    if (modelImagesContainer) {
                        // 更新显示已生成的图片
                        updateModelImages(modelImagesContainer, result.images, file.uniqueId);
                    }
                }
            }).catch(function(error) {
                console.error('获取已生成图片失败:', error);
            });
            
            // 从后端获取已生成的视频并显示
            window.pywebview.api.get_generated_videos(file.uniqueId).then(function(result) {
                if (result.success && result.videos && result.videos.length > 0) {
                    // 找到对应的视频容器
                    const videosContainer = row.querySelector('.generated-videos');
                    if (videosContainer) {
                        // 更新显示已生成的视频
                        updateVideo(videosContainer, result.videos, file.uniqueId);
                    }
                }
            }).catch(function(error) {
                console.error('获取已生成视频失败:', error);
            });
        }
        
        return row;
    } catch (error) {
        showToast('创建行元素时发生错误: ' + error.message, 'error');
        
        // 返回一个空的行元素
        const row = document.createElement('div');
        row.style.display = 'table-row';
        row.innerHTML = `
            <div style="display: table-cell; padding: 10px; width: 100%;" colspan="4">
                <div style="color: red;">创建行元素时发生错误: ${error.message}</div>
            </div>
        `;
        return row;
    }
}

/**
 * 生成视频
 */
function generateVideo(index) {
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        alert('API 不可用，请确保在WebView中运行此应用');
        return;
    }
    
    const file = window.currentFiles[index];
    if (!file) {
        showToast('文件不存在', 'error');
        return;
    }
    
    // 获取视频提示词
    const prompt = document.getElementById('video_prompt').value;
    if (!prompt) {
        showToast('请输入视频提示词', 'error');
        return;
    }
    
    // 获取模特图中的第一张图片作为视频生成的源图片
    let imageToUse = file.main_image; // 默认使用主图
    
    // 尝试获取已生成的模特图中的第一张
    if (file.uniqueId && typeof window.pywebview !== 'undefined' && window.pywebview.api) {
        // 同步获取已生成的图片列表
        window.pywebview.api.get_generated_images(file.uniqueId).then(function(result) {
            if (result.success && result.images && result.images.length > 0) {
                // 使用第一张模特图
                imageToUse = result.images[0];
                console.log('[DEBUG] Using first model image for video generation:', imageToUse);
            } else {
                console.log('[DEBUG] No model images found, using main image for video generation:', imageToUse);
            }
            
            // 显示正在生成的提示
            showToast('正在生成视频，请稍候...', 'info');
            
            // 调用后端生成视频
            window.pywebview.api.generate_video(imageToUse, prompt).then(function(result) {
                if (result.success) {
                    showToast('视频生成成功', 'success');
                    // 刷新文件夹内容显示
                    // importFolder();
                } else {
                    showToast('视频生成失败: ' + result.error, 'error');
                }
            }).catch(function(error) {
                showToast('视频生成异常: ' + error, 'error');
                console.error('视频生成异常:', error);
            });
        }).catch(function(error) {
            console.error('获取已生成图片失败，使用主图生成视频:', error);
            // 如果获取失败，仍然使用主图生成视频
            showToast('正在生成视频，请稍候...', 'info');
            
            // 调用后端生成视频
            window.pywebview.api.generate_video(imageToUse, prompt).then(function(result) {
                if (result.success) {
                    showToast('视频生成成功', 'success');
                    // 刷新文件夹内容显示
                    // importFolder();
                } else {
                    showToast('视频生成失败: ' + result.error, 'error');
                }
            }).catch(function(error) {
                showToast('视频生成异常: ' + error, 'error');
                console.error('视频生成异常:', error);
            });
        });
    } else {
        // 如果无法获取uniqueId或API不可用，直接使用主图生成视频
        console.log('[DEBUG] API not available or no uniqueId, using main image for video generation:', imageToUse);
        showToast('正在生成视频，请稍候...', 'info');
        
        // 调用后端生成视频
        window.pywebview.api.generate_video(imageToUse, prompt).then(function(result) {
            if (result.success) {
                showToast('视频生成成功', 'success');
                // 刷新文件夹内容显示
                // importFolder();
            } else {
                showToast('视频生成失败: ' + result.error, 'error');
            }
        }).catch(function(error) {
            showToast('视频生成异常: ' + error, 'error');
            console.error('视频生成异常:', error);
        });
    }
}

/**
 * 删除项目
 */
function deleteItem(index) {
    console.log('[DEBUG] deleteItem called with index:', index);
    console.log('[DEBUG] Current window.currentFiles:', window.currentFiles);
    
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        alert('API 不可用，请确保在WebView中运行此应用');
        return;
    }
    
    // 验证索引有效性
    if (!window.currentFiles) {
        console.error('[ERROR] window.currentFiles is null or undefined in deleteItem');
        showToast('文件列表未初始化', 'error');
        return;
    }
    
    if (index < 0 || index >= window.currentFiles.length) {
        console.error('[ERROR] Index out of range in deleteItem:', index, 'Length:', window.currentFiles.length);
        showToast('文件索引无效', 'error');
        return;
    }
    
    const file = window.currentFiles[index];
    console.log('[DEBUG] File to delete:', file);

    if (!file) {
        console.error('[ERROR] File is null at index:', index);
        showToast('文件不存在', 'error');
        return;
    }
    
    // 使用HTML5原生确认弹窗
    const confirmResult = confirm(`确定要删除 "${file.name}" 吗？`);
    if (!confirmResult) {
        console.log('[DEBUG] Delete cancelled by user');
        return;
    }
    
    // 调用后端删除项目
    console.log('[DEBUG] Calling backend delete_item with:', file.main_image);
    window.pywebview.api.delete_item(file.main_image).then(function(result) {
        console.log('[DEBUG] Backend delete response:', result);
        if (result.success) {
            showToast('删除成功', 'success');
            // 从列表中移除该项目
            window.currentFiles.splice(index, 1);
            console.log('[DEBUG] Removed item at index:', index, 'New length:', window.currentFiles.length);
            // 重新显示文件夹内容以更新索引
            displayFolderContent(window.currentFolderPath, window.currentFiles);
        } else {
            showToast('删除失败: ' + result.error, 'error');
        }
    }).catch(function(error) {
        console.error('[ERROR] Exception in deleteItem:', error);
        showToast('删除异常: ' + error, 'error');
    });
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

// 全局变量用于分页功能
window.currentPage = 1;
window.itemsPerPage = 50; // 每页显示50个项目

/**
 * 显示文件夹内容（分页版本）
 */
/*
function displayFolderContentWithPagination(folderPath, files) {
    console.log('显示文件夹内容（分页）:', folderPath, files);
    
    // 检查参数
    if (!folderPath || !files) {
        console.error('显示文件夹内容时参数缺失');
        showToast('显示文件夹内容时出现错误', 'error');
        return;
    }
    
    const tableBody = document.querySelector('#folder-content-table tbody');
    
    // 检查tableBody是否存在
    if (!tableBody) {
        console.error('无法找到文件夹内容表格');
        showToast('页面结构错误，无法显示文件夹内容', 'error');
        return;
    }
    
    // 清空现有内容
    tableBody.innerHTML = '';
    
    if (files.length === 0) {
        // 如果没有文件，显示提示信息
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="4" class="no-data">文件夹中没有图片文件</td>';
        tableBody.appendChild(row);
        return;
    }
    
    // 计算分页信息
    const totalPages = Math.ceil(files.length / window.itemsPerPage);
    const startIndex = (window.currentPage - 1) * window.itemsPerPage;
    const endIndex = Math.min(startIndex + window.itemsPerPage, files.length);
    const currentFiles = files.slice(startIndex, endIndex);
    
    // 添加每个文件到表格
    currentFiles.forEach(function(file, index) {
        const actualIndex = startIndex + index;
        console.log('处理文件:', file);
        const row = document.createElement('tr');
        // 为每一行添加data-index属性，方便后续定位
        row.setAttribute('data-index', actualIndex);
        
        // 创建4个模特图坑位（待生成）
        let modelImagesHtml = '';
        for (let i = 0; i < 4; i++) {
            modelImagesHtml += `<div style="width: 120px; height: 120px; border: 3px dashed #ccc; display: inline-flex; align-items: center; justify-content: center; margin: 5px; font-size: 14px; color: #999; border-radius: 6px; aspect-ratio: 9/16;">待生成</div>`;
        }
        
        // 创建1个视频坑位（待生成）
        let videosHtml = '';
        videosHtml += `<div style="width: 120px; height: 120px; border: 3px dashed #ccc; display: inline-flex; align-items: center; justify-content: center; margin: 5px; font-size: 14px; color: #999; border-radius: 6px; aspect-ratio: 9/16;">待生成</div>`;
        
        row.innerHTML = `
            <td>
                <img src="file://${file.main_image}" alt="主图" style="width: 120px; height: 120px; object-fit: cover; cursor: pointer; border-radius: 6px;" onclick="selectMainImage(${actualIndex})">
                <div style="margin-top: 5px; font-size: 12px;">点击选择</div>
            </td>
            <td>
                <div class="generated-images" data-item-index="${actualIndex}">
                    ${modelImagesHtml}
                </div>
            </td>
            <td>
                <div class="generated-videos">
                    ${videosHtml}
                </div>
            </td>
            <td>
                <div class="action-buttons">
                    <button class="btn btn-small btn-primary" onclick="generateImage(${actualIndex})">图片生成</button>
                    <button class="btn btn-small btn-secondary" onclick="generateVideo(${actualIndex})">视频生成</button>
                    <button class="btn btn-small btn-danger" onclick="deleteItem(${actualIndex})">删除</button>
                </div>
            </td>
        `;
        tableBody.appendChild(row);
    });
    
    // 添加分页控件
    const paginationRow = document.createElement('tr');
    paginationRow.innerHTML = `
        <td colspan="4" style="text-align: center; padding: 15px;">
            <div class="pagination-controls">
                <button class="btn btn-secondary" onclick="changePage(${window.currentPage - 1})" ${window.currentPage <= 1 ? 'disabled' : ''}>上一页</button>
                <span style="margin: 0 15px;">第 ${window.currentPage} 页，共 ${totalPages} 页</span>
                <button class="btn btn-secondary" onclick="changePage(${window.currentPage + 1})" ${window.currentPage >= totalPages ? 'disabled' : ''}>下一页</button>
                <span style="margin-left: 20px;">跳转到: </span>
                <input type="number" id="page-input" min="1" max="${totalPages}" value="${window.currentPage}" style="width: 60px; padding: 5px; margin: 0 5px;">
                <button class="btn btn-primary" onclick="goToPage()">跳转</button>
            </div>
        </td>
    `;
    tableBody.appendChild(paginationRow);
    
    // 保存当前文件夹路径和文件列表到全局变量
    window.currentFolderPath = folderPath;
    window.currentFiles = files;
    
    showToast(`成功导入文件夹，找到 ${files.length} 个子文件夹（当前显示第 ${window.currentPage} 页）`, 'success');
}
*/

/**
 * 切换页面
 */
/*
function changePage(page) {
    const totalPages = Math.ceil(window.currentFiles.length / window.itemsPerPage);
    if (page >= 1 && page <= totalPages) {
        window.currentPage = page;
        displayFolderContentWithPagination(window.currentFolderPath, window.currentFiles);
    }
}
*/

/**
 * 跳转到指定页面
 */
/*
function goToPage() {
    const pageInput = document.getElementById('page-input');
    const page = parseInt(pageInput.value);
    if (page && page >= 1) {
        changePage(page);
    } else {
        showToast('请输入有效的页码', 'error');
    }
}
*/

/**
 * 切换显示模式
 */
/*
function toggleDisplayMode() {
    // 检查必要的全局变量
    if (!window.currentFolderPath || !window.currentFiles) {
        showToast('没有可显示的文件夹内容', 'error');
        return;
    }
    
    const toggleButton = document.getElementById('toggle-display-mode');
    if (!toggleButton) {
        console.error('无法找到切换显示模式按钮');
        showToast('页面结构错误，无法切换显示模式', 'error');
        return;
    }
    
    if (toggleButton.textContent === '切换到分页模式') {
        // 切换到分页模式
        toggleButton.textContent = '切换到滚动模式';
        window.currentPage = 1;
        displayFolderContentWithPagination(window.currentFolderPath, window.currentFiles);
    } else {
        // 切换到虚拟滚动模式
        toggleButton.textContent = '切换到分页模式';
        displayFolderContent(window.currentFolderPath, window.currentFiles);
    }
}
*/
