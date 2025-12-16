# MetaSense Recruitment AI - Interactive Agent

An AI-powered healthcare recruitment system with **conversation monitoring** and **auto-recruiter connection** for MetaSense Inc.

## 🎯 Overview

This system helps healthcare recruiters manage candidate communications with AI assistance. The AI automatically responds to candidates, and when a candidate expresses interest in proceeding, they are automatically flagged for recruiter connection.

## ✨ Key Features

### Auto-Response with Monitoring
- ✅ **AI Auto-Responds** - Messages sent automatically (no delay)
- ✅ **Conversation Monitoring** - View all AI conversations in real-time
- ✅ **Auto-Recruiter Connection** - Candidates flagged when ready
- ✅ **Multiple Channels** - Handles both email and SMS communications

### Components
1. **FastAPI Backend** - RESTful API with webhook handlers
2. **Conversation Monitor** - Terminal-based viewer for AI conversations
3. **Database** - SQLite with full conversation history
4. **AI Agents** - GPT-4 powered conversation agents

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- Twilio account (for SMS)
- Email server credentials

### Installation

```bash
# Clone the repository
git clone https://github.com/skhann7201/metasense-recruitment-ai.git
cd metasense-recruitment-ai

# Install dependencies
pip install fastapi uvicorn sqlalchemy openai twilio requests python-dotenv

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials
```

### Running the System

**1. Start the Backend API:**
```bash
cd src/backend
python main.py
```

The API will be available at `http://localhost:8000`

**2. Launch the Conversation Monitor (Optional):**
```bash
cd src/backend
python conversation_monitor.py
```

## 📖 How It Works

### Automatic Response Flow
```
Candidate sends message → AI generates response → AUTO-SENT immediately
→ Logged in database → Recruiter can VIEW anytime
```

### When Candidate is Ready
```
Candidate says "yes, interested, ready, etc." → AI detects readiness
→ Status changed to "ready_for_recruiter" → AI adds recruiter contact info
→ Recruiter notified via monitoring dashboard
```

### Example Interaction

**Candidate:** "I'm interested in the ER position. What locations?"

**AI Response (auto-sent):** "Hi! We have ER positions in Camden and Cherry Hill..."

**Candidate:** "Sounds good, I'm interested!"

**AI Response (auto-sent):** "Excellent! [AI response]

---
🎉 Great! I'm connecting you with one of our recruiters who will reach out within 24 hours to discuss next steps. You can also call us directly at (856) 412-6100."

**Status:** Candidate marked as `ready_for_recruiter` ✅

## 🛠️ API Endpoints

### Webhooks (Receive Messages)
- `POST /api/webhooks/email-reply` - Handle incoming emails (auto-responds)
- `POST /api/webhooks/sms-reply` - Handle incoming SMS (auto-responds)

### Monitoring Endpoints
- `GET /api/conversations` - View all recent conversations
- `GET /api/conversations/candidate/{id}` - View specific candidate's conversation
- `GET /api/candidates/ready-for-recruiter` - List candidates ready for connection

### Other Endpoints
- `POST /api/campaigns/outreach` - Start recruitment campaign
- `GET /api/dashboard/stats` - System statistics
- `GET /api/candidates` - List candidates

## 💻 Conversation Monitor CLI

The CLI provides a simple interface for viewing what the AI is saying:

```
🏥 MetaSense Inc. - Conversation Monitor
══════════════════════════════════════════════════════════════════

OPTIONS:
  [1] View Recent Conversations
  [2] View Candidates Ready for Recruiter
  [3] View Specific Candidate Conversation
  [R] Refresh
  [Q] Quit
```

### Monitor Features
- **View Recent Conversations** - See latest AI interactions
- **Ready Candidates** - List of candidates waiting for recruiter call
- **Full Conversation History** - Complete thread for any candidate

## 📁 Project Structure

```
metasense-recruitment-ai/
├── src/
│   ├── backend/
│   │   ├── main.py                      # FastAPI application
│   │   ├── conversation_monitor.py      # CLI monitoring tool
│   │   ├── models/
│   │   │   └── database.py              # Database models
│   │   └── services/
│   │       ├── conversation_orchestrator.py # Response routing
│   │       ├── email_agent.py           # Email AI agent
│   │       └── sms_agent.py             # SMS AI agent
│   └── [legacy files...]
└── README.md                            # This file
```

## 🗄️ Database Schema

### Candidate
Healthcare candidate information and tracking
- Includes `status` field: "new", "engaged", "ready_for_recruiter", etc.

### Conversation
Complete message history for all communications
- `message_type`: "inbound" (from candidate) or "outbound" (AI response)
- `channel`: "email" or "sms"
- `content`: Full message text
- Timestamps for all messages

### Campaign
Outreach campaign tracking

## 🎯 Auto-Recruiter Connection

The system automatically detects when candidates are ready:

**Keywords that trigger connection:**
- "yes", "interested", "ready", "start", "proceed"
- "let's go", "sign me up", "i'm in", "sounds good"
- "let's do it", "when can we start"

**What happens:**
1. Candidate status changed to `ready_for_recruiter`
2. AI response includes recruiter contact info
3. Candidate appears in "Ready for Recruiter" list
4. Recruiter can call within 24 hours

## 🔒 Security & Compliance

- ✅ All conversations logged for review
- ✅ Unsubscribe handling built-in
- ✅ Complete audit trail
- ✅ Recruiter monitoring capabilities
- ✅ Auto-escalation when candidate is ready

## 📚 Key Differences

### What This System Does:
- ✅ **Auto-responds** - No delay, messages sent immediately
- ✅ **Monitors** - View what AI is saying anytime
- ✅ **Auto-connects** - Detects readiness and escalates to recruiter

### What This System Does NOT Do:
- ❌ **Approval workflow** - No approval required before sending
- ❌ **Message editing** - AI responses sent as-is
- ❌ **Manual intervention** - Fully automated unless recruiter connection needed

## 🤝 Contributing

This is a private repository for MetaSense Inc. internal use.

## 📄 License

Proprietary - MetaSense Inc.

## 🆘 Support

For questions or issues, contact the development team.

---

**Built with ❤️ for MetaSense Inc. Healthcare Recruitment**
