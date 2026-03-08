let ws = null;
let currentReportedMessage = ""; // 用于存储当前准备报告的消息

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeWebSocket();
});

function initializeWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsUrl = `${protocol}${window.location.host}/ws`;
    
    console.log('Attempting to connect to WebSocket:', wsUrl);
    
    ws = new WebSocket(wsUrl);

    ws.onopen = function(event) {
        console.log('WebSocket connection established.');
    };

    ws.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('Received WebSocket message:', data);

            // 根据消息类型处理不同的事件
            if (data.type === 'new_report') {
                // 处理新报告事件
                addReportToLog(data.payload);
            } else if (data.type === 'verification_result') {
                // 处理验证结果事件
                displayVerificationResult(data.payload);
            } else {
                console.warn('Unknown message type received via WebSocket:', data.type);
            }
        } catch (e) {
            console.error('Error parsing WebSocket message:', e, event.data);
        }
    };

    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
    };

    ws.onclose = function(event) {
        console.log('WebSocket connection closed. Code:', event.code, 'Reason:', event.reason);
        // 可选：实现重连逻辑
    };
}


function simulateSendMessage() {
    const messageInput = document.getElementById('message-input');
    const previewElement = document.getElementById('sent-message-preview');
    const message = messageInput.value.trim();

    if (!message) {
        alert("Please enter a message.");
        return;
    }

    currentReportedMessage = message; // 存储消息供后续报告使用
    document.getElementById('reported-msg').value = currentReportedMessage;

    previewElement.textContent = `Message simulated: "${currentReportedMessage}" sent from Alice to Bob.`;
    previewElement.style.color = 'green';

    // 清空输入框
    messageInput.value = '';
}

document.getElementById('report-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const reporterId = document.getElementById('reporter-select').value;
    const reportedMsg = document.getElementById('reported-msg').value;
    const context = document.getElementById('context-input').value;

    if (!reportedMsg) {
        alert("No message to report. Please simulate sending one first.");
        return;
    }

    const reportData = {
        reporter_id: reporterId,
        reported_message: reportedMsg,
        context: context
    };

    try {
        const response = await fetch('/api/v1/report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(reportData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('Report submitted successfully:', result);

        // 重置表单
        document.getElementById('reported-msg').value = '';
        document.getElementById('context-input').value = 'Violation Report';
        document.getElementById('sent-message-preview').textContent = 'Report submitted successfully. Awaiting moderation...';
        document.getElementById('sent-message-preview').style.color = 'blue';

    } catch (error) {
        console.error('Error submitting report:', error);
        alert('Failed to submit report. Check console for details.');
    }
});

function addReportToLog(reportData) {
    const container = document.getElementById('reports-container');
    const timestamp = new Date().toLocaleTimeString();
    const reportDiv = document.createElement('div');
    reportDiv.className = 'report-item';
    reportDiv.innerHTML = `
        <p><strong>[${timestamp}] New Report Received</strong></p>
        <p><strong>Context:</strong> ${reportData.context}</p>
        <p><strong>Encrypted Payload:</strong> ${reportData.c3_encrypted_payload.substring(0, 50)}...</p>
        <hr>
    `;
    container.prepend(reportDiv); // 添加到列表顶部
}

// 新增：处理并显示验证结果
function displayVerificationResult(resultData) {
    const container = document.getElementById('verification-results-container');
    const timestamp = new Date().toLocaleTimeString();

    const resultDiv = document.createElement('div');
    resultDiv.className = 'verification-result-item';

    // 根据验证结果设置样式
    if (resultData.is_valid) {
        resultDiv.classList.add('verification-success');
    } else {
        resultDiv.classList.add('verification-failed');
    }

    resultDiv.innerHTML = `
        <p><strong>[${timestamp}] Verification Result</strong></p>
        <p><strong>Status:</strong> <span class="${resultData.is_valid ? 'valid' : 'invalid'}">${resultData.is_valid ? 'VALID' : 'INVALID'}</span></p>
        ${resultData.message_content ? `<p><strong>Decrypted Message:</strong> "${resultData.message_content}"</p>` : ''}
        ${resultData.original_context ? `<p><strong>Original Context:</strong> ${resultData.original_context}</p>` : ''}
        ${resultData.error ? `<p><strong>Error:</strong> ${resultData.error}</p>` : ''}
        <p><strong>Sender Identity:</strong> ${resultData.sender_identity || 'Anonymized'}</p>
        <hr>
    `;

    container.prepend(resultDiv); // 添加到列表顶部
}