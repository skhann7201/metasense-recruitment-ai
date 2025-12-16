# MetaSense Recruitment AI - Interactive Agent

An AI-powered healthcare recruitment system with **interactive human-in-the-loop approval** for MetaSense Inc.

## 🎯 Overview

This system helps healthcare recruiters manage candidate communications with AI assistance while maintaining human oversight. Instead of auto-sending responses, the AI generates suggestions that recruiters can review, edit, and approve before sending.

## ✨ Key Features

### Interactive Approval Workflow
- ✅ **AI-Generated Responses** - Smart responses to candidate emails and SMS
- ✅ **Human Review Required** - No messages sent without recruiter approval
- ✅ **Edit Before Sending** - Personalize AI responses with your touch
- ✅ **Approval Queue** - Centralized queue of pending responses
- ✅ **Multiple Channels** - Handles both email and SMS communications

### Components
1. **FastAPI Backend** - RESTful API with webhook handlers
2. **Interactive CLI Tool** - Terminal-based response manager
3. **Database** - SQLite with conversation history and approval queue
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

**2. Launch the Interactive CLI:**
```bash
cd src/backend
python interactive_response_manager.py
```

**3. Try the Demo:**
```bash
python demo_interactive_workflow.py
```

## 📖 How It Works

### Old Workflow (Automated)
```
Candidate sends message → AI generates response → AUTO-SENT ⚡ (No review!)
```

### New Workflow (Interactive) ✅
```
Candidate sends message → AI generates response → QUEUED FOR APPROVAL 
→ Recruiter reviews/edits → Recruiter approves → SENT
```

### Example Session

1. **Candidate emails:** "I'm interested in the ER position. What locations?"

2. **AI generates:** "Hi! We have ER positions in Camden and Cherry Hill..."

3. **Queued for approval** - Response appears in pending queue

4. **Recruiter reviews** via CLI:
   - Sees candidate info, original message, AI response
   - Can approve as-is, edit first, or reject

5. **Approved and sent** - Email goes to candidate with tracking

## 🛠️ API Endpoints

### Webhooks (Receive Messages)
- `POST /api/webhooks/email-reply` - Handle incoming emails
- `POST /api/webhooks/sms-reply` - Handle incoming SMS

### Approval Workflow
- `GET /api/responses/pending` - List pending responses
- `POST /api/responses/{id}/approve` - Send approved response
- `PUT /api/responses/{id}/edit` - Edit response content
- `POST /api/responses/{id}/reject` - Reject/discard response

### Campaigns & Analytics
- `POST /api/campaigns/outreach` - Start recruitment campaign
- `GET /api/dashboard/stats` - System statistics
- `GET /api/candidates` - List candidates

## 💻 Interactive CLI Tool

The CLI provides a user-friendly interface for managing responses:

```
🏥 MetaSense Inc. - Interactive Response Manager
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Pending Responses: 3

[1] ID: 15 | EMAIL | Maria Rodriguez (ER Nurse)
[2] ID: 16 | SMS | James Wilson (Physical Therapist)
[3] ID: 17 | EMAIL | Lisa Thompson (Radiology Tech)

Your choice: 1

[Shows full details, AI response, and options to Approve/Edit/Reject]
```

### CLI Commands
- **[A]** Approve & Send
- **[E]** Edit Response
- **[R]** Reject/Discard
- **[B]** Back to List
- **[Q]** Quit

## 📁 Project Structure

```
metasense-recruitment-ai/
├── src/
│   ├── backend/
│   │   ├── main.py                          # FastAPI application
│   │   ├── interactive_response_manager.py  # CLI tool
│   │   ├── models/
│   │   │   └── database.py                  # Database models
│   │   └── services/
│   │       ├── conversation_orchestrator.py # Response routing
│   │       ├── email_agent.py               # Email AI agent
│   │       └── sms_agent.py                 # SMS AI agent
│   └── [legacy files...]
├── demo_interactive_workflow.py             # Demo script
├── INTERACTIVE_FEATURES.md                  # Feature documentation
├── WORKFLOW_DIAGRAM.md                      # Visual workflow
└── README.md                                # This file
```

## 🗄️ Database Schema

### PendingResponse (New!)
Stores AI-generated responses awaiting approval:
- `candidate_id` - Link to candidate
- `channel` - email or sms
- `incoming_message` - What candidate sent
- `generated_content` - AI's response
- `edited_content` - Recruiter's edits (if any)
- `status` - pending/approved/rejected/sent
- `reviewed_by` - Recruiter name
- `created_at`, `reviewed_at`, `sent_at` - Timestamps

### Candidate
Healthcare candidate information and tracking

### Conversation
Message history for all communications

### Campaign
Outreach campaign tracking

## 🔒 Security & Compliance

- ✅ Human review before any message is sent
- ✅ Unsubscribe handling built-in
- ✅ Audit trail (who reviewed/approved)
- ✅ No auto-sending without explicit approval
- ✅ Edit capability for compliance requirements

## 📚 Documentation

- **[INTERACTIVE_FEATURES.md](INTERACTIVE_FEATURES.md)** - Detailed feature guide
- **[WORKFLOW_DIAGRAM.md](WORKFLOW_DIAGRAM.md)** - Visual workflow comparison
- **[demo_interactive_workflow.py](demo_interactive_workflow.py)** - Working demo

## 🤝 Contributing

This is a private repository for MetaSense Inc. internal use.

## 📄 License

Proprietary - MetaSense Inc.

## 🆘 Support

For questions or issues, contact the development team.

---

**Built with ❤️ for MetaSense Inc. Healthcare Recruitment**
