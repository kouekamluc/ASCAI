# Real-Time Communication Setup Guide

## Overview
The platform now includes a complete real-time communication system using Django Channels and WebSockets. Users can:
- Chat with each other in real-time
- Receive instant notifications for forum replies
- See online/offline user status
- Get real-time updates for new threads and replies

## Installation Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

Make sure you have Redis running:
```bash
# On Windows (using WSL or Docker)
redis-server

# Or using Docker
docker run -d -p 6379:6379 redis:latest
```

### 2. Run Migrations
```bash
python manage.py makemigrations messaging
python manage.py migrate
```

### 3. Run the Server with Daphne
Since we're using Channels, you need to run the server with Daphne instead of the default Django server:

```bash
# Install daphne if not already installed
pip install daphne

# Run with daphne
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Or use manage.py
python manage.py runserver  # This should work if daphne is properly configured
```

## Features Implemented

### 1. Real-Time Chat (`/messaging/`)
- One-on-one conversations between users
- Real-time message delivery via WebSocket
- Online/offline user presence indicators
- Typing indicators
- Unread message counts
- Message history

### 2. Real-Time Forum Updates
- Instant notifications when someone replies to your thread
- Real-time reply updates for active thread viewers
- WebSocket integration for live updates

### 3. Notification System
- Browser notifications for new messages
- Toast notifications for forum replies
- Unread count badges

## Configuration

### Redis Configuration
Make sure Redis is running on `localhost:6379`. You can change this in `config/settings.py`:

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
```

### WebSocket URLs
WebSocket connections are available at:
- `/ws/chat/` - For chat functionality
- `/ws/notifications/` - For general notifications

## Usage

### Starting a Conversation
1. Navigate to `/messaging/`
2. Click on an online user or start a conversation from the members directory
3. Messages are sent and received in real-time

### Forum Real-Time Updates
- When viewing a thread, you'll automatically receive updates when new replies are posted
- Notifications appear for replies to your threads

## Troubleshooting

### WebSocket Connection Fails
1. Ensure Redis is running: `redis-cli ping` should return `PONG`
2. Check that daphne is being used instead of the default server
3. Verify `CHANNEL_LAYERS` configuration in settings

### Messages Not Appearing in Real-Time
1. Check browser console for WebSocket errors
2. Verify Redis connection
3. Check that channels middleware is properly configured

### Presence Indicators Not Working
1. Ensure UserPresence model is created and migrated
2. Check WebSocket connection status
3. Verify signals are firing correctly

## Development Notes

- WebSocket connections require authentication
- Messages are persisted in the database
- Presence is automatically updated when users connect/disconnect
- The system gracefully handles connection failures and reconnects











