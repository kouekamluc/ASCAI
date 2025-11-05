// Real-time Chat WebSocket Connection
class ChatConnection {
    constructor(conversationId = null) {
        this.conversationId = conversationId;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.typingTimeout = null;
        this.isTyping = false;
        this.pendingMessageId = null;
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/`;
        
        try {
            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = () => {
                // WebSocket connected
                this.reconnectAttempts = 0;
                console.log('WebSocket connected');
                
                if (this.conversationId) {
                    this.joinConversation(this.conversationId);
                }
                
                this.updateStatus('online');
            };
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.handleError('Failed to connect to chat server. Messages may not appear in real-time.');
            // Fallback: don't attempt reconnect if we can't even create the socket
            return;
        }

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        this.socket.onerror = (error) => {
            // WebSocket error - logged silently
            console.error('WebSocket error:', error);
            // Don't show error to user - will attempt reconnect on close
        };

        this.socket.onclose = (event) => {
            // WebSocket disconnected - will attempt reconnect
            console.log('WebSocket closed:', event.code, event.reason);
            this.updateStatus('offline');
            
            // Only reconnect if it wasn't a normal closure or intentional close
            if (event.code !== 1000 && event.code !== 1001) {
                this.attemptReconnect();
            }
        };
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            // Reconnecting - no user-facing message needed
            setTimeout(() => this.connect(), delay);
        }
    }

    joinConversation(conversationId) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            try {
                this.socket.send(JSON.stringify({
                    type: 'join_conversation',
                    conversation_id: conversationId
                }));
                this.conversationId = conversationId;
            } catch (error) {
                console.error('Error joining conversation:', error);
                this.handleError('Failed to join conversation.');
            }
        }
    }

    sendMessage(content) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN && this.conversationId) {
            try {
                const tempId = 'temp-' + Date.now();
                // Show message immediately as optimistic update
                this.displayMessage({
                    id: tempId,
                    sender_id: currentUserId,
                    content: content,
                    created_at: new Date().toISOString(),
                    is_read: false
                });
                
                this.socket.send(JSON.stringify({
                    type: 'send_message',
                    conversation_id: this.conversationId,
                    content: content
                }));
                
                // Store temp ID to replace later
                this.pendingMessageId = tempId;
            } catch (error) {
                console.error('Error sending message:', error);
                this.handleError('Failed to send message. Please try again.');
            }
        } else {
            // Fallback to AJAX if WebSocket is not available
            this.sendMessageAjax(content);
        }
    }
    
    async sendMessageAjax(content) {
        const formData = new FormData();
        formData.append('content', content);
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]')?.value || '');
        
        try {
            const response = await fetch(`/messaging/conversation/${this.conversationId}/send/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.displayMessage(data.message);
                }
            } else {
                this.handleError('Failed to send message. Please try again.');
            }
        } catch (error) {
            console.error('AJAX send error:', error);
            this.handleError('Failed to send message. Please check your connection.');
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
                // Mark message as read
                if (data.data.sender_id !== currentUserId) {
                    this.markAsRead();
                }
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
            case 'error':
                this.handleError(data.message);
                break;
            case 'joined_conversation':
                // Successfully joined conversation
                break;
        }
    }
    
    handleError(message) {
        console.error('Chat error:', message);
        // Show user-friendly error message
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'chat-error';
            errorDiv.style.cssText = 'padding: 0.5rem 1rem; background: #fee; color: #c33; border-radius: 8px; margin: 0.5rem 0;';
            errorDiv.textContent = message || 'An error occurred';
            messagesContainer.appendChild(errorDiv);
            setTimeout(() => errorDiv.remove(), 5000);
        }
    }
    
    markAsRead() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN && this.conversationId) {
            this.socket.send(JSON.stringify({
                type: 'mark_read',
                conversation_id: this.conversationId
            }));
        }
    }

    displayMessage(messageData) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;

        // Check if message already exists (avoid duplicates) - more robust check
        const messageId = String(messageData.id);
        const existingMessage = messagesContainer.querySelector(`[data-message-id="${messageId}"]`);
        if (existingMessage && !messageId.startsWith('temp-')) {
            // Message already exists, skip
            return;
        }
        
        // If we have a pending temp message and this is the real one from us, replace it
        if (this.pendingMessageId && messageData.sender_id === currentUserId && !messageId.startsWith('temp-')) {
            const tempMessage = messagesContainer.querySelector(`[data-message-id="${this.pendingMessageId}"]`);
            if (tempMessage) {
                tempMessage.remove();
                this.pendingMessageId = null;
            }
        }

        const messageDiv = document.createElement('div');
        const isSent = messageData.sender_id === currentUserId;
        messageDiv.className = `message ${isSent ? 'sent' : 'received'}`;
        messageDiv.setAttribute('data-message-id', messageId);
        
        // Convert line breaks to HTML
        const content = this.escapeHtml(messageData.content).replace(/\n/g, '<br>');
        
        messageDiv.innerHTML = `
            <div class="message-content">${content}</div>
            <div class="message-time">${new Date(messageData.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        
        // Update polling if it exists
        const pollDiv = document.getElementById('message-poll');
        if (pollDiv) {
            const currentUrl = pollDiv.getAttribute('hx-get');
            if (currentUrl) {
                const baseUrl = currentUrl.split('?')[0];
                pollDiv.setAttribute('hx-get', baseUrl + '?last_message_id=' + messageId);
            }
        }
        
        this.scrollToBottom();
    }
    
    scrollToBottom() {
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    showNotification(notificationData) {
        // Show browser notification or toast
        if ('Notification' in window && Notification.permission === 'granted') {
            const title = (typeof i18n !== 'undefined' && i18n.newMessageFrom) 
                ? `${i18n.newMessageFrom} ${notificationData.sender}`
                : `New message from ${notificationData.sender}`;
            new Notification(title, {
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
                if (typeof i18n !== 'undefined') {
                    statusText.textContent = data.is_online ? (i18n.online || 'Online') : (i18n.offline || 'Offline');
                } else {
                    statusText.textContent = data.is_online ? 'Online' : 'Offline';
                }
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
    
    async loadMoreMessages(page = 1) {
        if (!this.conversationId) return;
        
        try {
            const response = await fetch(`/messaging/conversation/${this.conversationId}/messages/?page=${page}&per_page=50`);
            if (response.ok) {
                const data = await response.json();
                const messagesContainer = document.getElementById('chat-messages');
                
                if (messagesContainer && data.messages.length > 0) {
                    // Store current scroll position
                    const oldScrollHeight = messagesContainer.scrollHeight;
                    const oldScrollTop = messagesContainer.scrollTop;
                    
                    // Prepend older messages
                    data.messages.forEach(msg => {
                        const messageDiv = document.createElement('div');
                        const isSent = msg.sender_id === currentUserId;
                        messageDiv.className = `message ${isSent ? 'sent' : 'received'}`;
                        messageDiv.setAttribute('data-message-id', msg.id);
                        
                        const content = this.escapeHtml(msg.content).replace(/\n/g, '<br>');
                        messageDiv.innerHTML = `
                            <div class="message-content">${content}</div>
                            <div class="message-time">${new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
                        `;
                        
                        messagesContainer.insertBefore(messageDiv, messagesContainer.firstChild);
                    });
                    
                    // Restore scroll position
                    const newScrollHeight = messagesContainer.scrollHeight;
                    messagesContainer.scrollTop = oldScrollTop + (newScrollHeight - oldScrollHeight);
                }
                
                return data.has_more;
            }
        } catch (error) {
            console.error('Error loading messages:', error);
        }
        return false;
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
    const messagesContainer = document.getElementById('chat-messages');
    
    // Initialize WebSocket connection
    if (typeof conversationId !== 'undefined' && conversationId !== null) {
        chatConnection = new ChatConnection(conversationId);
        chatConnection.connect();
        
        // Scroll to bottom on load
        if (messagesContainer) {
            setTimeout(() => chatConnection.scrollToBottom(), 100);
        }
        
        // Handle message form submission
        if (messageForm && messageInput) {
            messageForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const content = messageInput.value.trim();
                if (content) {
                    chatConnection.sendMessage(content);
                    messageInput.value = '';
                    chatConnection.sendTyping(false);
                    messageInput.style.height = 'auto';
                }
            });
            
            // Auto-resize textarea
            messageInput.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 150) + 'px';
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
            
            // Handle Enter key (Shift+Enter for new line)
            messageInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    messageForm.dispatchEvent(new Event('submit'));
                }
            });
        }
        
        // Load more messages on scroll to top
        if (messagesContainer) {
            let isLoading = false;
            messagesContainer.addEventListener('scroll', function() {
                if (messagesContainer.scrollTop < 100 && !isLoading) {
                    isLoading = true;
                    const currentPage = Math.floor(messagesContainer.children.length / 50) + 1;
                    chatConnection.loadMoreMessages(currentPage).then(hasMore => {
                        isLoading = false;
                    });
                }
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

