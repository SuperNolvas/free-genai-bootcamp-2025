// Debug utility for tracking Alpine.js state and initialization
const AlpineDebug = {
    logs: [],
    maxLogs: 100,
    debugPanel: null,

    init() {
        // Create debug panel
        this.debugPanel = document.createElement('div');
        this.debugPanel.id = 'alpine-debug-panel';
        this.debugPanel.style.cssText = `
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            max-height: 200px;
            background: rgba(0, 0, 0, 0.8);
            color: #fff;
            font-family: monospace;
            font-size: 12px;
            padding: 10px;
            overflow-y: auto;
            z-index: 9999;
        `;
        document.body.appendChild(this.debugPanel);

        // Add toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.textContent = 'Toggle Debug';
        toggleBtn.style.cssText = `
            position: fixed;
            bottom: 200px;
            left: 10px;
            z-index: 10000;
            padding: 5px;
            background: #333;
            color: #fff;
            border: none;
            border-radius: 4px;
        `;
        toggleBtn.onclick = () => this.togglePanel();
        document.body.appendChild(toggleBtn);

        // Initialize hidden
        this.debugPanel.style.display = 'none';
    },

    log(component, action, data = null) {
        const timestamp = new Date().toISOString();
        const logs = this.getLogs();
        
        logs.push({
            timestamp,
            component,
            action,
            data,
            refreshCount: this.getRefreshCount()
        });

        // Keep only the last maxLogs
        if (logs.length > this.maxLogs) {
            logs.splice(0, logs.length - this.maxLogs);
        }

        localStorage.setItem('alpineDebugLogs', JSON.stringify(logs));
        this.incrementRefreshCount();
        this.updatePanel();
    },

    getLogs() {
        try {
            return JSON.parse(localStorage.getItem('alpineDebugLogs') || '[]');
        } catch (e) {
            return [];
        }
    },

    getRefreshCount() {
        return parseInt(localStorage.getItem('alpineDebugRefreshCount') || '0', 10);
    },

    incrementRefreshCount() {
        const count = this.getRefreshCount() + 1;
        localStorage.setItem('alpineDebugRefreshCount', count.toString());
    },

    updatePanel() {
        if (!this.debugPanel) return;

        const logsHtml = this.getLogs().map(log => `
            <div style="margin-bottom: 5px; border-bottom: 1px solid #333;">
                <span style="color: #aaa;">${log.timestamp}</span>
                <span style="color: #4CAF50;">[${log.component}]</span>
                <span style="color: #2196F3;">${log.action}</span>
                ${log.data ? `<pre style="color: #FFC107">${JSON.stringify(log.data, null, 2)}</pre>` : ''}
            </div>
        `).join('');

        this.debugPanel.innerHTML = logsHtml;
        this.debugPanel.scrollTop = this.debugPanel.scrollHeight;
    },

    togglePanel() {
        if (this.debugPanel) {
            this.debugPanel.style.display = this.debugPanel.style.display === 'none' ? 'block' : 'none';
        }
    },

    clear() {
        this.clearLogs();
        this.updatePanel();
    },

    clearLogs() {
        localStorage.removeItem('alpineDebugLogs');
        localStorage.removeItem('alpineDebugRefreshCount');
    }
};

// Clear logs when holding Shift + D for 2 seconds
let keyPressTimer;
document.addEventListener('keydown', (e) => {
    if (e.shiftKey && e.key.toLowerCase() === 'd') {
        keyPressTimer = setTimeout(() => {
            AlpineDebug.clearLogs();
            console.log('Debug logs cleared');
        }, 2000);
    }
});

document.addEventListener('keyup', () => {
    clearTimeout(keyPressTimer);
});

// Initialize debug panel when the document is ready
document.addEventListener('DOMContentLoaded', () => {
    AlpineDebug.init();
});