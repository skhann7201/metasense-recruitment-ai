# Interactive Response Management

## Overview

The MetaSense Recruitment AI now includes an **Interactive Approval Workflow** that allows recruiters to review, edit, and approve AI-generated responses before they are sent to candidates.

## What Changed?

### Previously (Automated)
- Candidates sent emails/SMS → AI generated responses → Responses auto-sent immediately
- No human oversight or review

### Now (Interactive)
- Candidates send emails/SMS → AI generates responses → **Responses queued for approval** → Recruiter reviews/edits → Approved responses sent

## Components

### 1. Database Changes
Added `PendingResponse` table to store AI-generated responses awaiting approval:
- Stores candidate info, channel (email/SMS), incoming message
- Holds AI-generated content and optional human edits
- Tracks approval status: pending, approved, rejected, sent

### 2. Modified Webhook Handlers
Updated `/api/webhooks/email-reply` and `/api/webhooks/sms-reply`:
- Now **queue** responses instead of auto-sending
- Responses enter "pending" state requiring explicit approval

### 3. New API Endpoints

#### `GET /api/responses/pending`
List all responses awaiting approval with candidate context.

**Response:**
```json
{
  "success": true,
  "count": 2,
  "pending_responses": [
    {
      "id": 1,
      "candidate": {
        "name": "John Doe",
        "email": "john@example.com",
        "specialty": "Registered Nurse"
      },
      "channel": "email",
      "incoming_message": "I'm interested in the position...",
      "generated_content": "Hi John, thank you for your interest...",
      "created_at": "2025-12-16T10:30:00"
    }
  ]
}
```

#### `POST /api/responses/{id}/approve`
Approve and send a pending response.

**Request:**
```json
{
  "reviewer_name": "Sarah Johnson"
}
```

#### `POST /api/responses/{id}/reject`
Reject a response without sending.

**Request:**
```json
{
  "reviewer_name": "Sarah Johnson"
}
```

#### `PUT /api/responses/{id}/edit`
Edit response content before approval.

**Request:**
```json
{
  "edited_content": "Hi John, I appreciate your interest..."
}
```

### 4. Interactive CLI Tool

**File:** `src/backend/interactive_response_manager.py`

A terminal-based interface for recruiters to manage pending responses.

## Usage

### Starting the Backend API
```bash
cd src/backend
python main.py
```

### Running the Interactive CLI Manager
```bash
cd src/backend
python interactive_response_manager.py
```

### CLI Workflow

1. **Launch the tool** - Enter your name when prompted
2. **View pending responses** - See list of all responses awaiting review
3. **Select a response** - Enter the number to review details
4. **Review the response** - See:
   - Candidate information
   - Original message from candidate
   - AI-generated response
5. **Take action**:
   - **[A] Approve & Send** - Send the response as-is
   - **[E] Edit Response** - Modify the message before sending
   - **[R] Reject** - Discard without sending
   - **[B] Back to List** - Return to pending list

### Example CLI Session

```
🏥 MetaSense Inc. - Interactive Response Manager
==================================================================

📋 Pending Responses: 3

[1] ID: 15 | EMAIL
    Candidate: Maria Rodriguez
    Specialty: Emergency Room
    Email: maria.rodriguez@example.com
    Created: 2025-12-16 14:23:10

[2] ID: 16 | SMS
    Candidate: James Wilson
    Specialty: Physical Therapist
    Phone: +1215550112
    Created: 2025-12-16 14:25:33

Enter response number to review, 'R' to refresh, or 'Q' to quit
Your choice: 1

📧 Response Details (ID: 15)
==================================================================

👤 CANDIDATE INFORMATION:
   Name: Maria Rodriguez
   Profession: Registered Nurse
   Specialty: Emergency Room
   Location: Camden, NJ
   Email: maria.rodriguez@example.com

📱 CHANNEL: EMAIL
   Subject: Re: Healthcare Opportunities

💬 CANDIDATE'S MESSAGE:
----------------------------------------------------------------------
I'm very interested in learning more about the ER positions. What 
locations do you have available?
----------------------------------------------------------------------

🤖 AI-GENERATED RESPONSE:
----------------------------------------------------------------------
Hi Maria,

Thank you for your interest! We currently have several ER positions 
available in the Camden and Cherry Hill area. I'd love to discuss 
these opportunities with you in more detail.

Would you be available for a quick call this week to go over the 
specifics?

Best regards,
The MetaSense Team
----------------------------------------------------------------------

==================================================================
OPTIONS:
  [A] Approve & Send
  [E] Edit Response
  [R] Reject (Don't Send)
  [B] Back to List
==================================================================

Your choice: A

⚠️  Send this response? (yes/no): yes

✅ Response approved and sent successfully!
```

## Integration with Existing Workflow

1. **Candidate sends message** (email or SMS)
2. **Webhook receives** the message
3. **AI generates** response
4. **Response queued** in `pending_responses` table
5. **Recruiter reviews** via CLI or API
6. **Recruiter approves/edits/rejects**
7. **Approved responses sent** to candidates
8. **Conversation logged** as usual

## Benefits

- ✅ **Human oversight** - No automated responses without approval
- ✅ **Quality control** - Ensure professional, accurate responses
- ✅ **Personalization** - Edit AI responses for personal touch
- ✅ **Compliance** - Review before sending ensures regulatory compliance
- ✅ **Learning** - Understand what candidates are asking and how AI responds
- ✅ **Flexibility** - Approve, edit, or reject as needed

## API vs CLI

- **API endpoints** - For programmatic access, web UI integration
- **CLI tool** - For quick, terminal-based review by recruiters

Both methods access the same underlying approval queue.

## Notes

- Responses remain "pending" until explicitly approved or rejected
- Edited content takes precedence over original AI-generated content
- All actions are logged with reviewer name and timestamp
- The system maintains full conversation history as before
