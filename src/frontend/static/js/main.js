const ws = new WebSocket(`ws://localhost:8000/ws`);

document.getElementById('report-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const reporterId = document.getElementById('reporter-select').value;
    const reportedMsg = document.getElementById('reported-msg').value;
    const context = document.getElementById('context-input').value;

    if (!reportedMsg) {
        alert('Please simulate sending a message first.');
        return;
    }

    try {
        const response = await fetch('/api/v1/report', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({reporter_id: reporterId, reported_message: reportedMsg, context: context})
        });
        const data = await response.json();
        console.log('Report submitted:', data);
        // The WS will update the UI
    } catch (error) {
        console.error('Error submitting report:', error);
    }
});

function simulateSendMessage() {
    const msgInput = document.getElementById('message-input');
    const preview = document.getElementById('sent-message-preview');
    const reportMsgArea = document.getElementById('reported-msg');

    if (msgInput.value.trim() === '') {
        alert('Please enter a message to send.');
        return;
    }
    preview.textContent = `Simulated message sent from Alice to Bob: "${msgInput.value}"`;
    reportMsgArea.value = msgInput.value; // Pre-fill the report textarea
}

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'update_reports') {
        const container = document.getElementById('reports-container');
        container.innerHTML = '';
        data.data.forEach(report => {
            const div = document.createElement('div');
            div.className = 'report-item';
            let statusColor = '#28a745'; // Green for success
            if (report.status.includes('REJECTED')) statusColor = '#dc3545'; // Red for failure
            
            div.innerHTML = `
                <strong>ID:</strong> ${report.id}<br>
                <strong>Status:</strong> <span style="color:${statusColor}">${report.status}</span><br>
                <strong>Message:</strong> ${report.verification_result.message_content || 'N/A'}<br>
                <strong>Context:</strong> ${report.raw_report_data.context}<br>
                <small>${report.timestamp}</small>
            `;
            container.appendChild(div);
        });
    }
};

// Initial load of reports
fetch('/api/v1/reports')
    .then(response => response.json())
    .then(reports => {
        const container = document.getElementById('reports-container');
        reports.forEach(report => {
            const div = document.createElement('div');
            div.className = 'report-item';
             let statusColor = '#28a745';
            if (report.status.includes('REJECTED')) statusColor = '#dc3545';
            div.innerHTML = `
                <strong>ID:</strong> ${report.id}<br>
                <strong>Status:</strong> <span style="color:${statusColor}">${report.status}</span><br>
                <strong>Message:</strong> ${report.verification_result.message_content || 'N/A'}<br>
                <strong>Context:</strong> ${report.raw_report_data.context}<br>
                <small>${report.timestamp}</small>
            `;
            container.appendChild(div);
        });
    });