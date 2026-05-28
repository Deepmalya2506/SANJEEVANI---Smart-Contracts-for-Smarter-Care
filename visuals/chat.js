/**
 * SANJEEVANI MCP CLIENT — Chat System v2.0
 * Features:
 *  • Persistent session memory (localStorage + backend)
 *  • Beautiful message formatting & rendering
 *  • Embedded map visualization
 *  • Hospital authentication & context
 *  • Clear memory button with flash animation
 */

// ═════════════════════════════════════════
// STATE & CONFIGURATION
// ═════════════════════════════════════════

let currentSession = {
    id: localStorage.getItem('sessionId') || crypto.randomUUID(),
    hospitalId: localStorage.getItem('currentHospitalId') || null,
    hospitalName: localStorage.getItem('currentHospitalName') || null,
    authToken: localStorage.getItem('authToken') || null,
    messages: [],  // Full conversation history
};

// Sync session ID to localStorage
localStorage.setItem('sessionId', currentSession.id);

const MCP_API = 'http://127.0.0.1:9001';
const BACKEND_API = 'http://127.0.0.1:8000';

// ═════════════════════════════════════════
// AUTHENTICATION
// ═════════════════════════════════════════

async function hospitalLogin() {
    const hospitalId = document.getElementById('loginHospitalId')?.value;
    const email = document.getElementById('loginEmail')?.value;
    const password = document.getElementById('loginPassword')?.value;
    
    if (!hospitalId || !email || !password) {
        showToast('Please fill all fields', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${BACKEND_API}/hospitals/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                hospital_id: hospitalId,
                email: email,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            showToast(data.detail || 'Login failed', 'error');
            return;
        }
        
        // Store auth info
        currentSession.authToken = data.token;
        currentSession.hospitalId = hospitalId;
        currentSession.hospitalName = data.hospital.name;
        
        localStorage.setItem('authToken', data.token);
        localStorage.setItem('currentHospitalId', hospitalId);
        localStorage.setItem('currentHospitalName', data.hospital.name);
        
        // Close login modal and update UI
        document.getElementById('loginModal')?.classList.add('hidden');
        
        // Update topbar
        const topbar = document.querySelector('.mcp-topbar-title');
        if (topbar) {
            topbar.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/></svg>
                MCP Client — ${data.hospital.name}
            `;
        }
        
        showToast(`Logged in as ${data.hospital.name}`, 'success');
        
    } catch (error) {
        console.error('Login error:', error);
        showToast('Connection error during login', 'error');
    }
}

function checkAuthentication() {
    if (!currentSession.authToken || !currentSession.hospitalId) {
        showLoginModal();
        return false;
    }
    return true;
}

function showLoginModal() {
    const modal = document.getElementById('loginModal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

function closeLoginModal() {
    const modal = document.getElementById('loginModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// ═════════════════════════════════════════
// MEMORY MANAGEMENT
// ═════════════════════════════════════════

function loadSessionMemory() {
    const saved = localStorage.getItem(`session_${currentSession.id}`);
    if (saved) {
        currentSession.messages = JSON.parse(saved);
        return true;
    }
    return false;
}

function saveSessionMemory() {
    localStorage.setItem(`session_${currentSession.id}`, JSON.stringify(currentSession.messages));
}

function clearChatMemory() {
    const btn = document.querySelector('[onclick="clearChatMemory()"]');
    
    // Flash animation
    btn.style.animation = 'none';
    setTimeout(() => {
        btn.style.animation = 'flashClear 0.6s ease-in-out';
    }, 10);
    
    // Clear memory
    currentSession.messages = [];
    localStorage.removeItem(`session_${currentSession.id}`);
    
    // Reset UI
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.innerHTML = `
            <div class="chat-welcome" id="chatWelcome">
              <div class="chat-welcome-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/></svg>
              </div>
              <h3>MCP ASSISTANT</h3>
              <p>Memory cleared! Starting fresh conversation.</p>
            </div>
        `;
    }
    
    showToast('Chat memory cleared', 'success');
}

function getConversationContext() {
    return currentSession.messages.map(m => ({
        role: m.role,
        content: m.content
    }));
}

// ═════════════════════════════════════════
// CHAT MESSAGE RENDERING
// ═════════════════════════════════════════

function renderMessage(msg) {
    const container = document.getElementById('chatMessages');
    if (!container) return;

    // Remove welcome screen on first real message
    const welcomeScreen = document.getElementById('chatWelcome');
    if (welcomeScreen && msg.role !== 'system') {
        welcomeScreen.remove();
    }

    const msgEl = document.createElement('div');
    msgEl.className = `chat-msg ${msg.role}`;
    
    let html = '';
    
    if (msg.role === 'user') {
        html = `
            <div class="msg-sender">You</div>
            <div class="msg-bubble">${escapeHtml(msg.content)}</div>
        `;
    } else if (msg.role === 'ai') {
        html = `
            <div class="msg-sender">
                <div class="sender-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="3"/>
                        <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
                    </svg>
                </div>
                MCP Assistant
            </div>
            <div class="msg-bubble">${msg.content}</div>
        `;
    } else if (msg.type === 'approval') {
        html = `
            <div class="approval-card-msg">
                <div class="approval-header">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2v20M2 12h20"/>
                    </svg>
                    APPROVAL REQUIRED
                </div>
                <div class="approval-body">
                    <div class="proposal-row">
                        <div class="key">From Hospital</div>
                        <div class="val">${msg.data.from_hospital_name}</div>
                    </div>
                    <div class="proposal-row">
                        <div class="key">To Hospital</div>
                        <div class="val">${msg.data.to_hospital_name}</div>
                    </div>
                    <div class="proposal-row">
                        <div class="key">Equipment</div>
                        <div class="val">${msg.data.equipment_type} × ${msg.data.quantity}</div>
                    </div>
                    <div class="proposal-row">
                        <div class="key">Duration</div>
                        <div class="val">${msg.data.duration_hours} hours</div>
                    </div>
                    <div class="proposal-row">
                        <div class="key">Distance</div>
                        <div class="val">${(msg.data.distance_km || 'N/A').toFixed(1)} km</div>
                    </div>
                    <div class="proposal-row">
                        <div class="key">ETA</div>
                        <div class="val">~${Math.round(msg.data.eta_min || 0)} minutes</div>
                    </div>
                    <div class="approval-actions">
                        <button class="btn btn-primary btn-sm" onclick="approveDispatch('${msg.data.approval_id}')">Approve</button>
                        <button class="btn btn-ghost btn-sm" onclick="rejectDispatch('${msg.data.approval_id}')">Reject</button>
                    </div>
                </div>
            </div>
        `;
    } else if (msg.type === 'transaction') {
        html = `
            <div class="tx-badge-msg">
                <h4>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                    </svg>
                    ${msg.data.title || 'Transaction Confirmed'}
                </h4>
                <div class="tx-loan-id">Loan ID: #${msg.data.loan_id || 'N/A'}</div>
                <div class="tx-hash-val">${msg.data.tx_hash || 'N/A'}</div>
            </div>
        `;
    } else if (msg.type === 'map') {
        html = `
            <div class="map-embed-msg">
                <div class="map-header">🗺️ Route Map</div>
                <iframe src="${msg.data.map_url}" style="width:100%;height:400px;border:none;border-radius:8px;"></iframe>
            </div>
        `;
    } else if (msg.type === 'stage') {
        html = `
            <div class="stage-notif">
                <svg class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>
                </svg>
                ${msg.content}
            </div>
        `;
    }
    
    msgEl.innerHTML = html;
    container.appendChild(msgEl);
    container.scrollTop = container.scrollHeight;
}

// ═════════════════════════════════════════
// CHAT INTERACTION
// ═════════════════════════════════════════

async function sendChat() {
    // Check authentication
    if (!checkAuthentication()) {
        return;
    }
    
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) {
        return;
    }
    
    // Add user message to memory
    const userMsg = { role: 'user', content: message, timestamp: new Date() };
    currentSession.messages.push(userMsg);
    renderMessage(userMsg);
    
    // Clear input
    input.value = '';
    input.style.height = 'auto';
    
    // Show typing indicator
    const typing = document.createElement('div');
    typing.className = 'typing-indicator';
    typing.id = 'typingIndicator';
    typing.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
    document.getElementById('chatMessages').appendChild(typing);
    
    try {
        const response = await fetch(`${MCP_API}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                session_id: currentSession.id,
                hospital_id: currentSession.hospitalId,
                auth_token: currentSession.authToken,
                conversation_history: getConversationContext()
            })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        document.getElementById('typingIndicator')?.remove();
        
        if (data.approval_required) {
            // Add approval message
            const approvalMsg = {
                type: 'approval',
                role: 'system',
                data: data.loan_proposal,
                timestamp: new Date()
            };
            currentSession.messages.push(approvalMsg);
            renderMessage(approvalMsg);
        } else if (data.error) {
            showToast(`Error: ${data.error}`, 'error');
        } else {
            // Add AI response
            const aiMsg = { role: 'ai', content: data.reply || 'Processing...', timestamp: new Date() };
            currentSession.messages.push(aiMsg);
            renderMessage(aiMsg);
            
            // Handle map URL if present
            if (data.route_map_url) {
                const mapMsg = {
                    type: 'map',
                    role: 'system',
                    data: { map_url: data.route_map_url },
                    timestamp: new Date()
                };
                currentSession.messages.push(mapMsg);
                renderMessage(mapMsg);
            }
            
            // Handle transaction confirmation
            if (data.tx_hash) {
                const txMsg = {
                    type: 'transaction',
                    role: 'system',
                    data: {
                        title: 'Loan Created On-Chain',
                        loan_id: data.loan_id,
                        tx_hash: data.tx_hash
                    },
                    timestamp: new Date()
                };
                currentSession.messages.push(txMsg);
                renderMessage(txMsg);
            }
        }
        
        // Save memory
        saveSessionMemory();
        
    } catch (error) {
        console.error('Chat error:', error);
        showToast('Connection error', 'error');
        document.getElementById('typingIndicator')?.remove();
    }
}

function handleChatKey(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendChat();
    }
}

function autoResizeTA(el) {
    el.style.height = 'auto';
    el.style.height = (el.scrollHeight) + 'px';
}

// ═════════════════════════════════════════
// SUGGESTION PILLS & QUICK ACTIONS
// ═════════════════════════════════════════

function useSuggestion(el) {
    const text = el.innerText;
    const input = document.getElementById('chatInput');
    input.value = text;
    input.focus();
}

async function approveDispatch(approvalId) {
    try {
        const response = await fetch(`${MCP_API}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                approval_id: approvalId,
                session_id: currentSession.id,
                auth_token: currentSession.authToken
            })
        });
        
        const data = await response.json();
        
        if (data.tx_hash) {
            const msg = {
                type: 'transaction',
                role: 'system',
                data: { title: 'Dispatch Approved', loan_id: data.loan_id, tx_hash: data.tx_hash },
                timestamp: new Date()
            };
            currentSession.messages.push(msg);
            renderMessage(msg);
            saveSessionMemory();
            showToast('Dispatch approved!', 'success');
        }
    } catch (error) {
        console.error('Approval error:', error);
        showToast('Approval failed', 'error');
    }
}

function rejectDispatch(approvalId) {
    const msg = {
        role: 'ai',
        content: '❌ Dispatch rejected by user.',
        timestamp: new Date()
    };
    currentSession.messages.push(msg);
    renderMessage(msg);
    saveSessionMemory();
    showToast('Dispatch rejected', 'success');
}

// ═════════════════════════════════════════
// HOSPITAL SELECTION & LOADING
// ═════════════════════════════════════════

async function loadHospitals() {
    try {
        const response = await fetch(`${BACKEND_API}/hospitals`);
        const hospitals = await response.json();
        
        const container = document.getElementById('hospitalLoginDropdown');
        if (container) {
            container.innerHTML = hospitals.map(h => `
                <option value="${h.id}">${h.name} (${h.location?.lat.toFixed(2)}°, ${h.location?.lon.toFixed(2)}°)</option>
            `).join('');
        }
    } catch (error) {
        console.error('Hospital loading error:', error);
    }
}

// ═════════════════════════════════════════
// UTILITY FUNCTIONS
// ═════════════════════════════════════════

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function showToast(message, type = 'info') {
    const container = document.querySelector('.toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            ${type === 'success' ? '<polyline points="20 6 9 17 4 12"></polyline>' : 
              type === 'error' ? '<circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line>' :
              '<circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>'}
        </svg>
        ${escapeHtml(message)}
    `;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'toastOut 0.25s ease forwards';
        setTimeout(() => toast.remove(), 250);
    }, 4000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

function newChat() {
    if (!checkAuthentication()) return;
    
    currentSession.id = crypto.randomUUID();
    currentSession.messages = [];
    localStorage.setItem('sessionId', currentSession.id);
    
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.innerHTML = `
            <div class="chat-welcome" id="chatWelcome">
              <div class="chat-welcome-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/></svg>
              </div>
              <h3>MCP ASSISTANT</h3>
              <p>New conversation started. How can I help you today?</p>
            </div>
        `;
    }
}

// ═════════════════════════════════════════
// INITIALIZATION
// ═════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    // Load hospital list for login dropdown
    loadHospitals();
    
    // Check if already authenticated
    if (currentSession.authToken && currentSession.hospitalId) {
        loadSessionMemory();
        
        // Update topbar with hospital name
        const topbar = document.querySelector('.mcp-topbar-title');
        if (topbar) {
            topbar.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/></svg>
                MCP Client — ${currentSession.hospitalName || 'Loading...'}
            `;
        }
    } else {
        // Show login modal
        showLoginModal();
    }
});