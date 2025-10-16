# Project Architecture Map

**Project**: Harbour Space Student Life Companion  
**Version**: 1.0  
**Last Updated**: October 15, 2025

---

## Table of Contents

1. [Overview](#1-overview)
   - 1.1 [Purpose](#11-purpose)
   - 1.2 [Architecture Style](#12-architecture-style)
2. [System Architecture](#2-system-architecture)
3. [Application Components](#3-application-components)
   - 3.1 [harbour-space-app (Next.js)](#31-harbour-space-app-nextjs)
     - 3.1.1 [Core Features](#311-core-features)
     - 3.1.2 [Routing Structure](#312-routing-structure)
   - 3.2 [student-life-companion (Python API)](#32-student-life-companion-python-api)
     - 3.2.1 [Core Features](#321-core-features)
     - 3.2.2 [API Endpoints](#322-api-endpoints)
4. [Technology Stack](#4-technology-stack)
   - 4.1 [Frontend Stack](#41-frontend-stack)
   - 4.2 [Backend Stack (Next.js API)](#42-backend-stack-nextjs-api)
   - 4.3 [AI Service Stack](#43-ai-service-stack)
   - 4.4 [DevOps & Tools](#44-devops--tools)
5. [Data Models](#5-data-models)
   - 5.1 [MongoDB Schemas](#51-mongodb-schemas)
     - 5.1.1 [User Model](#511-user-model)
     - 5.1.2 [Course Model](#512-course-model)
     - 5.1.3 [Schedule Model](#513-schedule-model)
     - 5.1.4 [ScheduleEntry Model](#514-scheduleentry-model)
     - 5.1.5 [Message Model (Chat)](#515-message-model-chat)
     - 5.1.6 [Group Model](#516-group-model)
     - 5.1.7 [GroupMessage Model](#517-groupmessage-model)
   - 5.2 [SQLite Schema (AI Service)](#52-sqlite-schema-ai-service)
     - 5.2.1 [Query History Table](#521-query-history-table)
6. [Authentication & Authorization](#6-authentication--authorization)
   - 6.1 [Authentication Flow](#61-authentication-flow)
   - 6.2 [Authorization Middleware](#62-authorization-middleware)
   - 6.3 [Role-Based Permissions](#63-role-based-permissions)
7. [API Architecture](#7-api-architecture)
   - 7.1 [Next.js API Routes](#71-nextjs-api-routes)
     - 7.1.1 [Authentication APIs](#711-authentication-apis)
     - 7.1.2 [Admin APIs](#712-admin-apis)
     - 7.1.3 [Student APIs](#713-student-apis)
   - 7.2 [FastAPI Endpoints (AI Service)](#72-fastapi-endpoints-ai-service)
8. [Real-time Communication](#8-real-time-communication)
   - 8.1 [WebSocket Server Architecture](#81-websocket-server-architecture)
     - 8.1.1 [Connection Flow](#811-connection-flow)
     - 8.1.2 [Message Types](#812-message-types)
   - 8.2 [Client-Side WebSocket Integration](#82-client-side-websocket-integration)
9. [Database Architecture](#9-database-architecture)
   - 9.1 [MongoDB Configuration](#91-mongodb-configuration)
   - 9.2 [Connection Configuration](#92-connection-configuration)
   - 9.3 [Data Relationships](#93-data-relationships)
10. [Deployment & Infrastructure](#10-deployment--infrastructure)
    - 10.1 [Development Environment](#101-development-environment)
    - 10.2 [Environment Variables](#102-environment-variables)
      - 10.2.1 [Next.js App (.env.local)](#1021-nextjs-app-envlocal)
      - 10.2.2 [AI Service (.env)](#1022-ai-service-env)
    - 10.3 [Production Considerations](#103-production-considerations)
11. [Directory Structure](#11-directory-structure)
    - 11.1 [harbour-space-app](#111-harbour-space-app)
    - 11.2 [student-life-companion](#112-student-life-companion)
12. [Data Flow Diagrams](#12-data-flow-diagrams)
    - 12.1 [User Registration Flow](#121-user-registration-flow)
    - 12.2 [Admin CRUD Flow](#122-admin-crud-flow)
    - 12.3 [Chat Message Flow](#123-chat-message-flow)
    - 12.4 [AI Chatbot Flow](#124-ai-chatbot-flow)
13. [Security Architecture](#13-security-architecture)
    - 13.1 [Security Measures](#131-security-measures)
    - 13.2 [Password Security](#132-password-security)
    - 13.3 [Environment Secrets](#133-environment-secrets)
14. [Integration Points](#14-integration-points)
    - 14.1 [Next.js ↔ MongoDB](#141-nextjs--mongodb)
    - 14.2 [Next.js ↔ WebSocket Server](#142-nextjs--websocket-server)
    - 14.3 [Student Portal ↔ AI Service](#143-student-portal--ai-service)
    - 14.4 [Client ↔ Next.js API](#144-client--nextjs-api)
15. [Future Enhancements](#15-future-enhancements)
    - 15.1 [Planned Features](#151-planned-features)
    - 15.2 [Technical Improvements](#152-technical-improvements)
    - 15.3 [AI Enhancements](#153-ai-enhancements)
16. [Appendix](#16-appendix)
    - 16.1 [Key Files Reference](#161-key-files-reference)
    - 16.2 [Port Reference](#162-port-reference)
    - 16.3 [External Services](#163-external-services)

---

## 1. Overview

The project consists of two main applications working together to provide a comprehensive student life management system:

### 1.1 Purpose
- **Admin Portal**: Management interface for courses, schedules, and students
- **Student Portal**: Interactive platform with chatbot, community features, and schedule management
- **AI Assistant**: Intelligent Q&A system for student life queries (visa, housing, university)

### 1.2 Architecture Style
- **Frontend**: Server-Side Rendered (SSR) with Next.js 15
- **Backend**: RESTful APIs + WebSocket for real-time features
- **AI Service**: FastAPI microservice with ML capabilities
- **Database**: MongoDB (NoSQL) + SQLite (AI service)

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  Web Browser (React/Next.js Frontend)                           │
│  - Admin Dashboard                                               │
│  - Student Portal                                                │
│  - Authentication Pages                                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTPS/WSS
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐    ┌────────────────────────────────┐ │
│  │  Next.js Server     │    │  WebSocket Server (Node.js)    │ │
│  │  - SSR/API Routes   │    │  - Real-time Chat              │ │
│  │  - Middleware       │    │  - Group Messaging             │ │
│  │  - NextAuth         │    │  - Live Updates                │ │
│  │  Port: 3000         │    │  Port: 3001                    │ │
│  └─────────────────────┘    └────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI Service (Python)                                │  │
│  │  - AI Chatbot API                                        │  │
│  │  - Semantic Search Engine                                │  │
│  │  - Groq LLM Integration                                  │  │
│  │  Port: 8000                                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐    ┌────────────────────────────────┐ │
│  │  MongoDB            │    │  SQLite                        │ │
│  │  - Users            │    │  - Chat History                │ │
│  │  - Courses          │    │  - Query Logs                  │ │
│  │  - Schedules        │    │  - Ratings                     │ │
│  │  - Messages         │    │                                │ │
│  │  - Groups           │    │                                │ │
│  │  Port: 27017        │    │  File-based                    │ │
│  └─────────────────────┘    └────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Application Components

### 3.1 harbour-space-app (Next.js)

#### 3.1.1 Core Features
- **Authentication System** (NextAuth.js)
  - Credential-based login
  - Role-based access control (Admin/Student)
  - Session management
  - First user auto-admin assignment

- **Admin Panel**
  - User Management (CRUD)
  - Course Management (CRUD)
  - Schedule Management (CRUD)
  - Dashboard with statistics

- **Student Portal**
  - Personal Dashboard
  - Schedule Viewer
  - Chat System (1-to-1 messaging)
  - Community Groups
  - AI Chatbot Integration

#### 3.1.2 Routing Structure
```
/                          → Landing/Home Page
/auth/signin              → Login Page
/auth/signup              → Registration Page
/admin/*                  → Admin Routes (Protected)
  /admin                  → Admin Dashboard
  /admin/users            → User Management
  /admin/courses          → Course Management
  /admin/schedules        → Schedule Management
/student/*                → Student Routes (Protected)
  /student                → Student Dashboard
  /student/schedule       → Personal Schedule
  /student/chat           → Direct Messaging
  /student/community      → Group Discussions
  /student/community/:id  → Specific Group Chat
```

### 3.2 student-life-companion (Python API)

#### 3.2.1 Core Features
- **Semantic Search Engine**
  - TF-IDF vectorization
  - Cosine similarity matching
  - 42+ curated Q&A pairs

- **AI Integration**
  - Groq API (Llama 3.1 70B)
  - Fallback for unknown queries
  - Context-aware responses

- **Knowledge Management**
  - Topic categorization (Visa, Housing, University, etc.)
  - Rating system (👍/👎)
  - Popular questions tracking
  - Query history with SQLite

#### 3.2.2 API Endpoints
```
GET  /                    → Health check
GET  /ask                 → Ask a question
GET  /history             → Get query history
GET  /reload              → Reload knowledge base
POST /rate                → Rate an answer
GET  /topics              → Get all topics
GET  /popular             → Get popular questions
```

---

## 4. Technology Stack

### 4.1 Frontend Stack
| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 15.0.2 | React framework with SSR |
| React | 18.x | UI library |
| TypeScript | 5.x | Type safety |
| Tailwind CSS | 3.4.1 | Styling framework |
| NextAuth.js | 4.24.11 | Authentication |

### 4.2 Backend Stack (Next.js API)
| Technology | Version | Purpose |
|------------|---------|---------|
| Node.js | 20+ | Runtime environment |
| MongoDB | Latest | Primary database |
| Mongoose | 8.19.1 | ODM for MongoDB |
| bcryptjs | 3.0.2 | Password hashing |
| WebSocket (ws) | 8.18.3 | Real-time communication |

### 4.3 AI Service Stack
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.8+ | Runtime |
| FastAPI | Latest | Web framework |
| scikit-learn | Latest | ML algorithms |
| Groq API | Latest | LLM integration |
| SQLite | 3.x | Query history |
| Uvicorn | Latest | ASGI server |

### 4.4 DevOps & Tools
| Technology | Purpose |
|------------|---------|
| Docker | MongoDB containerization |
| Docker Compose | Service orchestration |
| ESLint | Code linting |
| Git | Version control |

---

## 5. Data Models

### 5.1 MongoDB Schemas

#### 5.1.1 User Model
```typescript
{
  _id: ObjectId,
  name: string,
  email: string (unique, indexed),
  password: string (hashed),
  role: 'admin' | 'student',
  enrollmentDate: Date,
  program?: string,
  year?: number,
  createdAt: Date,
  updatedAt: Date
}
```

#### 5.1.2 Course Model
```typescript
{
  _id: ObjectId,
  name: string,
  code: string (unique),
  description?: string,
  credits: number,
  instructor: string,
  department: string,
  createdAt: Date,
  updatedAt: Date
}
```

#### 5.1.3 Schedule Model
```typescript
{
  _id: ObjectId,
  student: ObjectId (ref: User),
  course: ObjectId (ref: Course),
  semester: string,
  year: number,
  startDate: Date,
  endDate: Date,
  createdAt: Date,
  updatedAt: Date
}
```

#### 5.1.4 ScheduleEntry Model
```typescript
{
  _id: ObjectId,
  schedule: ObjectId (ref: Schedule),
  dayOfWeek: string,
  startTime: string,
  endTime: string,
  location?: string,
  type: 'lecture' | 'lab' | 'tutorial',
  createdAt: Date,
  updatedAt: Date
}
```

#### 5.1.5 Message Model (Chat)
```typescript
{
  _id: ObjectId,
  sender: ObjectId (ref: User),
  receiver: ObjectId (ref: User),
  content: string,
  timestamp: Date,
  read: boolean,
  createdAt: Date
}
```

#### 5.1.6 Group Model
```typescript
{
  _id: ObjectId,
  name: string,
  description: string,
  creator: ObjectId (ref: User),
  members: [ObjectId] (ref: User),
  isPublic: boolean,
  createdAt: Date,
  updatedAt: Date
}
```

#### 5.1.7 GroupMessage Model
```typescript
{
  _id: ObjectId,
  group: ObjectId (ref: Group),
  sender: ObjectId (ref: User),
  content: string,
  timestamp: Date,
  createdAt: Date
}
```

### 5.2 SQLite Schema (AI Service)

#### 5.2.1 Query History Table
```sql
CREATE TABLE query_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  query TEXT NOT NULL,
  answer TEXT NOT NULL,
  source TEXT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  rating INTEGER DEFAULT 0,
  topic TEXT
);
```

---

## 6. Authentication & Authorization

### 6.1 Authentication Flow

```
┌─────────┐
│  User   │
└────┬────┘
     │ 1. Submit credentials
     ↓
┌────────────────────┐
│  /api/auth/signin  │
└────┬───────────────┘
     │ 2. Validate credentials
     ↓
┌────────────────────┐
│   MongoDB Query    │
│   - Find user      │
│   - Check password │
└────┬───────────────┘
     │ 3. Create session
     ↓
┌────────────────────┐
│   NextAuth.js      │
│   - Generate JWT   │
│   - Set cookie     │
└────┬───────────────┘
     │ 4. Return token
     ↓
┌─────────┐
│ Client  │
│ Session │
└─────────┘
```

### 6.2 Authorization Middleware

**File**: `middleware.ts`

- **Protected Routes**: `/admin/*`, `/student/*`
- **Admin Access**: Only users with `role: 'admin'`
- **Student Access**: Only users with `role: 'student'`
- **Auto-redirect**: Unauthorized users redirected to home

### 6.3 Role-Based Permissions

| Role | Admin Panel | Student Portal | API Access |
|------|-------------|----------------|------------|
| Admin | ✅ Full | ❌ No | Admin APIs |
| Student | ❌ No | ✅ Full | Student APIs |
| Guest | ❌ No | ❌ No | Public only |

---

## 7. API Architecture

### 7.1 Next.js API Routes

#### 7.1.1 Authentication APIs
```
POST /api/auth/signup        → Register new user
POST /api/auth/[...nextauth] → NextAuth handlers
```

#### 7.1.2 Admin APIs
```
# Users
GET    /api/admin/users        → List all users
POST   /api/admin/users        → Create user
PUT    /api/admin/users/[id]   → Update user
DELETE /api/admin/users/[id]   → Delete user

# Courses
GET    /api/admin/courses      → List all courses
POST   /api/admin/courses      → Create course
PUT    /api/admin/courses/[id] → Update course
DELETE /api/admin/courses/[id] → Delete course

# Schedules
GET    /api/admin/schedules    → List all schedules
POST   /api/admin/schedules    → Create schedule
PUT    /api/admin/schedules/[id] → Update schedule
DELETE /api/admin/schedules/[id] → Delete schedule
```

#### 7.1.3 Student APIs
```
# Chat
GET  /api/chat/users           → Get chat users
POST /api/chat/message         → Send message
GET  /api/chat/history         → Get message history

# Groups
GET  /api/groups               → List user's groups
POST /api/groups               → Create group
GET  /api/groups/available     → List public groups
POST /api/groups/[id]/join     → Join group
GET  /api/groups/[id]/messages → Get group messages
POST /api/groups/[id]/messages → Send group message

# Schedule
GET  /api/schedule             → Get user's schedule
```

### 7.2 FastAPI Endpoints (AI Service)

```
GET  /                    → Health check
GET  /ask?query={text}    → Ask chatbot question
GET  /history?limit={n}   → Get query history
GET  /reload              → Reload knowledge base
POST /rate                → Rate answer (👍/👎)
GET  /topics              → Get topic categories
GET  /popular             → Get popular questions
```

---

## 8. Real-time Communication

### 8.1 WebSocket Server Architecture

**File**: `server.js`  
**Port**: 3001

#### 8.1.1 Connection Flow
```
1. Client connects to ws://localhost:3001
2. Client registers with user ID
3. Server stores connection in Map<userId, WebSocket>
4. Client can send/receive messages
5. Server routes messages to specific users
```

#### 8.1.2 Message Types
```typescript
// Register user
{
  type: 'register',
  userId: string
}

// Chat message (1-to-1)
{
  type: 'chat-message',
  senderId: string,
  receiverId: string,
  senderName: string,
  content: string,
  timestamp: Date
}

// Group message
{
  type: 'group-message',
  groupId: string,
  senderId: string,
  senderName: string,
  content: string,
  members: string[],
  timestamp: Date
}
```

### 8.2 Client-Side WebSocket Integration

- **Component**: `ChatbotWidget.tsx`, Chat pages
- **Auto-reconnect**: Implemented
- **Message persistence**: Stored in MongoDB
- **Real-time updates**: Live message delivery

---

## 9. Database Architecture

### 9.1 MongoDB Configuration

```yaml
# Docker Compose Setup
services:
  mongodb:
    image: mongo:latest
    container_name: harbour-space-mongodb
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: admin123
      MONGO_INITDB_DATABASE: harbour-space
```

### 9.2 Connection Configuration

```typescript
// lib/mongodb.ts
MONGODB_URI=mongodb://admin:admin123@localhost:27017/harbour-space?authSource=admin
```

### 9.3 Data Relationships

```
User (1) ──────→ (N) Schedule
User (1) ──────→ (N) Message (as sender)
User (1) ──────→ (N) Message (as receiver)
User (1) ──────→ (N) Group (as creator)
User (N) ←────→ (N) Group (as member)
Course (1) ─────→ (N) Schedule
Schedule (1) ───→ (N) ScheduleEntry
Group (1) ──────→ (N) GroupMessage
```

---

## 10. Deployment & Infrastructure

### 10.1 Development Environment

```bash
# Start MongoDB
docker-compose up -d

# Start Next.js (Port 3000)
npm run dev

# Start WebSocket Server (Port 3001)
npm run ws

# Start both concurrently
npm run dev:all

# Start AI Service (Port 8000)
cd student-life-companion
uvicorn main:app --reload
```

### 10.2 Environment Variables

#### 10.2.1 Next.js App (.env.local)
```env
MONGODB_URI=mongodb://admin:admin123@localhost:27017/harbour-space?authSource=admin
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=<generated-secret>
NODE_ENV=development
WS_PORT=3001
```

#### 10.2.2 AI Service (.env)
```env
GROQ_API_KEY=<your-groq-api-key>
```

### 10.3 Production Considerations

- [ ] NEXTAUTH_SECRET: Generate secure key
- [ ] MongoDB: Use MongoDB Atlas or production server
- [ ] HTTPS: Enable SSL/TLS
- [ ] WebSocket: WSS protocol
- [ ] CORS: Configure allowed origins
- [ ] Rate Limiting: Implement API throttling
- [ ] Logging: Add monitoring and error tracking
- [ ] Backup: Automated database backups

---

## 11. Directory Structure

### 11.1 harbour-space-app

```
harbour-space-app/
├── app/                      # Next.js App Router
│   ├── globals.css          # Global styles
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Home page
│   ├── admin/               # Admin routes
│   │   ├── layout.tsx       # Admin layout (sidebar)
│   │   ├── page.tsx         # Admin dashboard
│   │   ├── users/           # User management
│   │   ├── courses/         # Course management
│   │   └── schedules/       # Schedule management
│   ├── student/             # Student routes
│   │   ├── layout.tsx       # Student layout
│   │   ├── page.tsx         # Student dashboard
│   │   ├── chat/            # Chat interface
│   │   ├── community/       # Group discussions
│   │   └── schedule/        # Schedule viewer
│   ├── auth/                # Authentication pages
│   │   ├── signin/          # Login page
│   │   └── signup/          # Registration page
│   └── api/                 # API routes
│       ├── auth/            # Auth APIs
│       ├── admin/           # Admin APIs
│       ├── chat/            # Chat APIs
│       ├── groups/          # Group APIs
│       └── schedule/        # Schedule APIs
├── components/              # React components
│   ├── AuthProvider.tsx    # Auth context
│   ├── ChatbotWidget.tsx   # AI chatbot
│   ├── CourseForm.tsx      # Course form
│   ├── ScheduleForm.tsx    # Schedule form
│   ├── UserForm.tsx        # User form
│   └── Modal.tsx           # Modal component
├── lib/                     # Utilities
│   ├── auth.ts             # Auth config
│   ├── adminAuth.ts        # Admin auth helpers
│   ├── mongodb.ts          # DB connection
│   └── seedAdmin.ts        # Admin seeding
├── models/                  # Mongoose models
│   ├── User.ts
│   ├── Course.ts
│   ├── Schedule.ts
│   ├── ScheduleEntry.ts
│   ├── Message.ts
│   ├── Group.ts
│   └── GroupMessage.ts
├── types/                   # TypeScript types
│   └── next-auth.d.ts
├── public/                  # Static assets
├── scripts/                 # Utility scripts
│   └── seedAdmin.js
├── middleware.ts            # Next.js middleware (auth)
├── server.js               # WebSocket server
├── docker-compose.yml      # MongoDB setup
├── next.config.ts          # Next.js config
├── tailwind.config.ts      # Tailwind config
├── tsconfig.json           # TypeScript config
└── package.json            # Dependencies
```

### 11.2 student-life-companion

```
student-life-companion/
├── main.py                     # FastAPI application
├── data_ingestion.py          # Data processing scripts
├── knowledge_base.json        # Q&A knowledge base
├── knowledge_base_two.json    # Additional Q&A
├── knowledge_base_encrypted.json # Encrypted data
├── users_encrypted.py         # User encryption utils
├── requirements.txt           # Python dependencies
├── static/
│   └── frontend.html          # Web interface
├── __pycache__/               # Python cache
├── GROQ_SETUP.md             # Groq API setup guide
├── README.md                 # Documentation
└── LICENSE                   # License file
```

---

## 12. Data Flow Diagrams

### 12.1 User Registration Flow

```
┌──────┐      ┌─────────────┐      ┌──────────┐      ┌─────────┐
│Client│─────→│/api/auth/   │─────→│ bcryptjs │─────→│ MongoDB │
│      │      │  signup     │      │  hash    │      │         │
└──────┘      └─────────────┘      └──────────┘      └─────────┘
    ↑                                                       │
    └───────────────────────────────────────────────────────┘
                    Return success/error
```

### 12.2 Admin CRUD Flow

```
┌──────┐      ┌──────────┐      ┌─────────────┐      ┌─────────┐
│Admin │─────→│Middleware│─────→│API Route    │─────→│ MongoDB │
│Panel │      │(Auth)    │      │/api/admin/* │      │         │
└──────┘      └──────────┘      └─────────────┘      └─────────┘
    ↑              │                    │                   │
    │              │ Check role         │                   │
    │              └────────────────────┘                   │
    └─────────────────────────────────────────────────────┘
                    Return data/error
```

### 12.3 Chat Message Flow

```
┌────────┐   ┌──────────┐   ┌─────────┐   ┌──────────┐   ┌─────────┐
│Sender  │──→│WebSocket │──→│ MongoDB │   │WebSocket │──→│Receiver │
│Client  │   │ Server   │   │(persist)│   │ Server   │   │ Client  │
└────────┘   └──────────┘   └─────────┘   └──────────┘   └─────────┘
     │            │                              │              │
     │ Send msg   │ Store                   Route msg     Display
     └────────────┘                              │              │
                                                 └──────────────┘
```

### 12.4 AI Chatbot Flow

```
┌──────┐   ┌─────────┐   ┌───────────┐   ┌──────────┐   ┌─────────┐
│User  │──→│FastAPI  │──→│TF-IDF     │──→│Knowledge │   │         │
│Query │   │/ask     │   │Search     │   │Base      │   │         │
└──────┘   └─────────┘   └───────────┘   └──────────┘   │         │
    ↑           │              │                │         │         │
    │           │              │ No match?      │         │  Groq   │
    │           │              └────────────────┼────────→│  LLM    │
    │           │                               │         │  API    │
    │           ↓                               ↓         └─────────┘
    └───────Response ←────────────────────────────────────────┘
         (store in SQLite)
```

---

## 13. Security Architecture

### 13.1 Security Measures

| Layer | Security Feature | Implementation |
|-------|-----------------|----------------|
| **Authentication** | Password Hashing | bcryptjs (10 rounds) |
| | Session Management | NextAuth.js JWT |
| | CSRF Protection | NextAuth built-in |
| **Authorization** | Role-Based Access | Middleware checks |
| | Route Protection | Next.js middleware |
| **Data** | Input Validation | Mongoose schemas |
| | SQL Injection | Mongoose ODM |
| | XSS Prevention | React escaping |
| **Network** | HTTPS | Required in production |
| | WebSocket Security | WSS in production |
| | CORS | Configured origins |
| **API** | Rate Limiting | To be implemented |
| | API Keys | Groq API (env vars) |

### 13.2 Password Security

```typescript
// Registration
const hashedPassword = await bcrypt.hash(password, 10);

// Login
const isValid = await bcrypt.compare(password, hashedPassword);
```

### 13.3 Environment Secrets

```bash
# Never commit these
MONGODB_URI=<secret>
NEXTAUTH_SECRET=<secret>
GROQ_API_KEY=<secret>
```

---

## 14. Integration Points

### 14.1 Next.js ↔ MongoDB
- **Library**: Mongoose
- **Connection**: Persistent connection pooling
- **Models**: Typed schemas with validation

### 14.2 Next.js ↔ WebSocket Server
- **Protocol**: WebSocket (ws)
- **Port**: 3001
- **Communication**: Bidirectional real-time

### 14.3 Student Portal ↔ AI Service
- **Protocol**: HTTP REST
- **Port**: 8000
- **Component**: ChatbotWidget
- **Endpoints**: `/ask`, `/history`, `/rate`

### 14.4 Client ↔ Next.js API
- **Protocol**: HTTP/HTTPS
- **Format**: JSON
- **Authentication**: JWT via NextAuth

---

## 15. Future Enhancements

### 15.1 Planned Features
- [ ] Email notifications (schedule changes, messages)
- [ ] File upload/sharing in groups
- [ ] Video call integration
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Attendance tracking
- [ ] Grade management system
- [ ] Calendar integration (Google Calendar, iCal)
- [ ] Push notifications
- [ ] Multi-language support

### 15.2 Technical Improvements
- [ ] Redis caching layer
- [ ] GraphQL API option
- [ ] Microservices architecture
- [ ] Kubernetes deployment
- [ ] CI/CD pipeline
- [ ] Automated testing (Jest, Playwright)
- [ ] Performance monitoring (New Relic, DataDog)
- [ ] Error tracking (Sentry)
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Load balancing

### 15.3 AI Enhancements
- [ ] Voice input/output
- [ ] Multilingual support
- [ ] Personalized recommendations
- [ ] Sentiment analysis
- [ ] Document Q&A (upload PDFs)
- [ ] Integration with university systems
- [ ] Proactive notifications
- [ ] Study group matching

---

## 16. Appendix

### 16.1 Key Files Reference

| File | Purpose | Location |
|------|---------|----------|
| `middleware.ts` | Route protection | `/harbour-space-app/` |
| `server.js` | WebSocket server | `/harbour-space-app/` |
| `main.py` | AI service | `/student-life-companion/` |
| `lib/mongodb.ts` | DB connection | `/harbour-space-app/lib/` |
| `lib/auth.ts` | Auth config | `/harbour-space-app/lib/` |

### 16.2 Port Reference

| Service | Port | Protocol |
|---------|------|----------|
| Next.js Dev Server | 3000 | HTTP |
| WebSocket Server | 3001 | WS/WSS |
| FastAPI Service | 8000 | HTTP |
| MongoDB | 27017 | MongoDB |

### 16.3 External Services

| Service | Purpose | Documentation |
|---------|---------|---------------|
| Groq API | LLM inference | https://console.groq.com/ |
| MongoDB Atlas | Cloud database | https://www.mongodb.com/cloud/atlas |
| NextAuth | Authentication | https://next-auth.js.org/ |

---

**Document Version**: 1.0  
**Generated**: October 15, 2025  
**Maintained By**: Development Team  
**Review Cycle**: Quarterly
