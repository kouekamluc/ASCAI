// Real-time Chat WebSocket Connection
class ChatConnection {
    constructor(conversationId = null) {
        this.conversationId = conversationId;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.typingTimeout = null;
        this.isTyping = false;
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/`;
        
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            
            if (this.conversationId) {
                this.joinConversation(this.conversationId);
            }
            
            this.updateStatus('online');
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.socket.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateStatus('offline');
            this.attemptReconnect();
        };
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
            setTimeout(() => this.connect(), delay);
        }
    }

    joinConversation(conversationId) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'join_conversation',
                conversation_id: conversationId
            }));
            this.conversationId = conversationId;
        }
    }

    sendMessage(content) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN && this.conversationId) {
            this.socket.send(JSON.stringify({
                type: 'send_message',
                conversation_id: this.conversationId,
                content: content
            }));
        }
    }

    sendTyping(isTyping) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN && this.conversationId) {
            if (this.isTyping !== isTyping) {
                this.isTyping = isTyping;
                this.socket.send(JSON.stringify({
                    type: 'typing',
                    conversation_id: this.conversationId,
                    is_typing: isTyping
                }));
            }
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'message':
                this.displayMessage(data.data);
                break;
            case 'notification':
                this.showNotification(data.data);
                break;
            case 'presence':
                this.updatePresence(data);
                break;
            case 'typing':
                this.showTypingIndicator(data);
                break;
        }
    }

    displayMessage(messageData) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;

        const messageDiv = document.createElement('div');
        const isSent = messageData.sender_id === currentUserId;
        messageDiv.className = `message ${isSent ? 'sent' : 'received'}`;
        
        messageDiv.innerHTML = `
            <div class="message-content">${this.escapeHtml(messageData.content)}</div>
            <div class="message-time">${new Date(messageData.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showNotification(notificationData) {
        // Show browser notification or toast
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(`New message from ${notificationData.sender}`, {
                body: notificationData.content,
                icon: '/static/images/logo.png'
            });
        }
        
        // Update unread count if on chat list page
        this.updateUnreadCount();
    }

    updatePresence(data) {
        if (data.user_id === otherUserId) {
            const indicator = document.getElementById('status-indicator');
            const statusText = document.getElementById('status-text');
            
            if (indicator && statusText) {
                indicator.className = `status-indicator ${data.is_online ? 'online' : 'offline'}`;
                statusText.textContent = data.is_online ? '{% trans "Online" %}' : '{% trans "Offline" %}';
            }
        }
    }

    showTypingIndicator(data) {
        if (data.user_id !== currentUserId) {
            const indicator = document.getElementById('typing-indicator');
            if (indicator) {
                indicator.style.display = data.is_typing ? 'block' : 'none';
            }
        }
    }

    updateStatus(status) {
        // Update connection status if needed
    }

    updateUnreadCount() {
        // Update unread badge in navigation
        const badge = document.querySelector('.unread-count');
        if (badge) {
            const current = parseInt(badge.textContent) || 0;
            badge.textContent = current + 1;
            badge.style.display = 'inline-block';
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
        }
    }
}

// Initialize chat when page loads
let chatConnection = null;

document.addEventListener('DOMContentLoaded', function() {
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    
    // Initialize WebSocket connection
    if (typeof conversationId !== 'undefined' && conversationId !== null) {
        chatConnection = new ChatConnection(conversationId);
        chatConnection.connect();
        
        // Handle message form submission
        if (messageForm && messageInput) {
            messageForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const content = messageInput.value.trim();
                if (content) {
                    chatConnection.sendMessage(content);
                    messageInput.value = '';
                    chatConnection.sendTyping(false);
                }
            });
            
            // Handle typing indicator
            let typingTimer;
            messageInput.addEventListener('input', function() {
                clearTimeout(typingTimer);
                chatConnection.sendTyping(true);
                
                typingTimer = setTimeout(() => {
                    chatConnection.sendTyping(false);
                }, 2000);
            });
        }
    }
    
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (chatConnection) {
        chatConnection.disconnect();
    }
});

