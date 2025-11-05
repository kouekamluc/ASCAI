# 🎯 ASCAI Platform - Quick Visual Reference

Quick reference guide for understanding the platform at a glance.

---

## 🏛️ System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    ASCAI SaaS Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Users   │  │ Members  │  │  News    │  │  Events   │  │
│  │          │  │          │  │          │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Documents │  │   Jobs   │  │  Forums  │  │Messaging │  │
│  │          │  │          │  │          │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
│  ┌──────────┐  ┌──────────┐                               │
│  │ Payments │  │Dashboard │                               │
│  │          │  │          │                               │
│  └──────────┘  └──────────┘                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 👥 User Roles Hierarchy

```
                    ┌─────────────┐
                    │    Admin    │  ← Full System Access
                    │  (Highest)   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Board     │  ← Content Management
                    │   Member    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Member    │  ← Standard User
                    │             │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Public    │  ← Limited Access
                    │  (Lowest)   │
                    └─────────────┘
```

---

## 📦 Module Overview

| Module | Purpose | Key Features |
|--------|---------|--------------|
| **accounts** | User Management | Registration, Login, Profiles |
| **members** | Member Directory | Search, Filter, Applications |
| **news** | News & Announcements | Publishing, Categories, Visibility |
| **events** | Event Management | Calendar, RSVP, Registration |
| **documents** | File Library | Upload, Versioning, Folders |
| **jobs** | Job Board | Postings, Applications |
| **forums** | Discussions | Threads, Replies, Moderation |
| **messaging** | Real-time Chat | Conversations, WebSockets |
| **payments** | Payment Processing | Membership Fees |
| **dashboard** | Analytics | Reports, Statistics |

---

## 🔄 Common User Flows

### Registration Flow
```
Visit Site → Register → Email Verification → Login → Dashboard
```

### Member Application Flow
```
Public User → Apply → Admin Review → Approval → Member Status
```

### Event Registration Flow
```
Browse Events → View Details → Register → Confirmation → Attend
```

### News Publishing Flow
```
Board/Admin → Create Post → Set Visibility → Publish → Public View
```

---

## 🔐 Permission Matrix

| Feature | Public | Member | Board | Admin |
|---------|--------|--------|-------|-------|
| View Public News | ✅ | ✅ | ✅ | ✅ |
| View Member News | ❌ | ✅ | ✅ | ✅ |
| View Member Directory | ❌ | ✅ | ✅ | ✅ |
| Edit Own Profile | ❌ | ✅ | ✅ | ✅ |
| Create News | ❌ | ❌ | ✅ | ✅ |
| Manage Events | ❌ | ❌ | ✅ | ✅ |
| Manage Users | ❌ | ❌ | ❌ | ✅ |
| System Config | ❌ | ❌ | ❌ | ✅ |

---

## 📊 Database Schema (Simplified)

```
User (1) ──── (1) Member
  │
  ├─── (many) NewsPost
  ├─── (many) Event (organizer)
  ├─── (many) EventRegistration
  ├─── (many) JobPosting
  ├─── (many) Thread
  ├─── (many) Reply
  └─── (many) Message

Member (1) ──── (many) MemberAchievement
            ──── (many) MemberApplication

Event (1) ──── (many) EventRegistration
         ──── (many) EventReminder

DocumentFolder (1) ──── (many) Document
Document (1) ──── (many) DocumentVersion

Category (1) ──── (many) Thread
Thread (1) ──── (many) Reply

Conversation (many) ──── (many) User
Conversation (1) ──── (many) Message
```

---

## 🛣️ URL Patterns Quick Reference

```
/                           → Dashboard Home
/accounts/                  → Authentication
  ├── register/             → User Registration
  ├── login/                → User Login
  ├── logout/               → User Logout
  └── profile/              → User Profile

/members/                   → Member Directory
  ├── profile/<id>/         → Member Profile
  ├── apply/                → Membership Application
  └── pay/                  → Membership Payment

/news/                      → News & Announcements
  ├── list/                 → News List
  └── <slug>/               → News Detail

/events/                     → Events
  ├── list/                 → Event List
  ├── <slug>/                → Event Detail
  └── <slug>/register/      → Event Registration

/documents/                  → Document Library
  ├── list/                 → Document List
  └── <id>/                 → Document Detail

/jobs/                       → Job Board
  ├── list/                 → Job List
  └── <slug>/                → Job Detail

/forums/                     → Discussion Forums
  ├── category/<slug>/      → Category View
  └── thread/<slug>/        → Thread View

/messaging/                  → Messaging
  ├── conversations/        → Conversation List
  └── chat/<id>/            → Chat Interface

/dashboard/admin/            → Admin Dashboard
```

---

## 🎨 Design System Colors

```
Primary Green:  #1B5E20  ████████  (Unity & Growth)
Primary Red:    #B71C1C  ████████  (Passion & Energy)
Accent Yellow:  #FFB300  ████████  (Optimism)
Accent Blue:    #003082  ████████  (Trust & Stability)
```

---

## 🔧 Technology Stack

```
Frontend:     Django Templates + HTMX + CSS
Backend:      Django 5.1+ (Python)
Database:     PostgreSQL
Cache:        Redis
Real-time:    Django Channels (WebSockets)
Rich Text:    CKEditor
i18n:         Django i18n (EN, FR, IT)
```

---

## 📈 Status Indicators

- ✅ **Complete** - Fully implemented and tested
- 🔄 **In Progress** - Currently being developed
- 📅 **Planned** - Scheduled for future development

---

## 🚀 Quick Start Commands

```bash
# Start development server
python manage.py runserver

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Compile translations
python manage.py compilemessages
```

---

**Last Updated**: 2024  
**Version**: 0.35

