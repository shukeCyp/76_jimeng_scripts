/**
 * WebView应用前端脚本
 * 处理前端交互和与Python后端的通信
 */

// 页面加载完成
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成');

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
});

/**
 * 加载应用信息
 */
function loadAppInfo() {
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        alert('API 不可用，请确保在WebView中运行此应用');
        return;
    }

    // 调用后端的 get_info 方法
    window.pywebview.api.get_info().then(function(response) {
        // 更新DOM显示应用信息
        document.getElementById('appName').textContent = response.app_name;
        document.getElementById('appVersion').textContent = response.version;
        document.getElementById('appPlatform').textContent = response.platform;

        console.log('成功加载应用信息');
    }).catch(function(error) {
        console.error('加载应用信息失败:', error);
        alert('加载应用信息失败: ' + error);
    });
}

/**
 * 执行计算操作
 * @param {string} operation - 操作类型: add, subtract, multiply, divide
 */
function calculate(operation) {
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        alert('API 不可用，请确保在WebView中运行此应用');
        return;
    }

    // 获取输入值
    const num1 = parseFloat(document.getElementById('num1').value);
    const num2 = parseFloat(document.getElementById('num2').value);
    const resultElement = document.getElementById('result');

    // 验证输入
    if (isNaN(num1) || isNaN(num2)) {
        resultElement.textContent = '请输入有效的数字';
        resultElement.style.color = '#dc3545';
        return;
    }

    // 调用后端的 perform_calculation 方法
    window.pywebview.api.perform_calculation(num1, num2, operation).then(function(response) {
        if (response.success) {
            // 格式化结果显示
            const result = typeof response.result === 'number'
                ? response.result.toFixed(2)
                : response.result;
            resultElement.textContent = result;
            resultElement.style.color = '#28a745';
            console.log('计算成功:', result);
        } else {
            resultElement.textContent = '错误: ' + response.error;
            resultElement.style.color = '#dc3545';
            console.error('计算失败:', response.error);
        }
    }).catch(function(error) {
        resultElement.textContent = '计算出错: ' + error;
        resultElement.style.color = '#dc3545';
        console.error('计算异常:', error);
    });
}

/**
 * 发送消息到后端
 */
function sendMessage() {
    // 检查API是否可用
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        alert('API 不可用，请确保在WebView中运行此应用');
        return;
    }

    // 获取输入值
    const input = document.getElementById('messageInput').value.trim();
    const resultElement = document.getElementById('messageResult');

    // 验证输入
    if (!input) {
        resultElement.textContent = '请输入消息';
        resultElement.classList.remove('show');
        return;
    }

    // 调用后端的 log_message 方法
    window.pywebview.api.log_message(input).then(function(response) {
        resultElement.textContent = response;
        resultElement.classList.add('show');
        document.getElementById('messageInput').value = '';
        console.log('消息已发送:', response);
    }).catch(function(error) {
        resultElement.textContent = '发送失败: ' + error;
        resultElement.classList.add('show');
        console.error('发送消息失败:', error);
    });
}

/**
 * 回车快速发送消息
 */
document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        });
    }
});

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
