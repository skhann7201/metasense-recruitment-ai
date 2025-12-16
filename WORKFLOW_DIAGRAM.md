# Interactive Agent Workflow - Visual Comparison

## BEFORE: Automated (No Human Review)

```
┌─────────────┐
│  Candidate  │
│   Sends     │
│   Email/    │
│    SMS      │
└─────┬───────┘
      │
      ▼
┌─────────────────┐
│  Webhook        │
│  Receives       │
│  Message        │
└─────┬───────────┘
      │
      ▼
┌─────────────────┐
│   AI Agent      │
│   Generates     │
│   Response      │
└─────┬───────────┘
      │
      ▼
┌─────────────────┐
│  IMMEDIATELY    │ ⚠️  NO HUMAN REVIEW
│  AUTO-SEND      │
│  Response       │
└─────┬───────────┘
      │
      ▼
┌─────────────────┐
│  Candidate      │
│  Receives       │
│  Response       │
└─────────────────┘
```

## AFTER: Interactive (Human-in-the-Loop)

```
┌─────────────┐
│  Candidate  │
│   Sends     │
│   Email/    │
│    SMS      │
└─────┬───────┘
      │
      ▼
┌─────────────────┐
│  Webhook        │
│  Receives       │
│  Message        │
└─────┬───────────┘
      │
      ▼
┌─────────────────┐
│   AI Agent      │
│   Generates     │
│   Response      │
└─────┬───────────┘
      │
      ▼
┌─────────────────┐
│  QUEUE FOR      │ ✅ PENDING APPROVAL
│  APPROVAL       │
│  (Database)     │
└─────┬───────────┘
      │
      │     ┌──────────────────────────┐
      │     │  Recruiter Reviews via   │
      │────►│  • Interactive CLI       │
      │     │  • API Endpoints         │
      │     │  • (Future: Web UI)      │
      │     └──────┬───────────────────┘
      │            │
      │            ▼
      │     ┌──────────────────────────┐
      │     │  Review Options:         │
      │     │  [A] Approve & Send      │
      │     │  [E] Edit First          │
      │     │  [R] Reject/Discard      │
      │     └──────┬───────────────────┘
      │            │
      │            ▼
      │     ┌──────────────────────────┐
      │     │  If Approved:            │
      └────►│  Send Response           │
            └──────┬───────────────────┘
                   │
                   ▼
            ┌─────────────────┐
            │  Candidate      │
            │  Receives       │
            │  Response       │
            └─────────────────┘
```

## Key Differences

### Automated (Before)
- ❌ No human oversight
- ❌ No quality control
- ❌ No personalization opportunity  
- ❌ Cannot catch AI errors
- ❌ No compliance review
- ⚡ Instant (but potentially problematic)

### Interactive (After)  
- ✅ Human reviews every response
- ✅ Quality assurance built-in
- ✅ Can personalize/edit responses
- ✅ Catch and fix AI mistakes
- ✅ Ensure compliance before sending
- ✅ Learn from AI suggestions
- ⏱️  Slight delay (but controlled)

## Approval Workflow Details

```
┌────────────────────────────────────────────────────────────┐
│                     APPROVAL QUEUE                          │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Response #1: Maria Rodriguez (ER Nurse) - Email           │
│  AI Generated: "Hi Maria, thank you for your interest..."  │
│  Status: PENDING                                            │
│  Actions: [Approve] [Edit] [Reject]                        │
│                                                             │
│  Response #2: James Wilson (PT) - SMS                      │
│  AI Generated: "Hey James! We have some great PT roles..." │
│  Status: PENDING                                            │
│  Actions: [Approve] [Edit] [Reject]                        │
│                                                             │
│  Response #3: Lisa Thompson (Radiology) - Email            │
│  AI Generated: "Hello Lisa, I'd love to discuss MRI..."    │
│  Status: PENDING → EDITED → APPROVED → SENT ✅             │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

## Database Schema

```sql
CREATE TABLE pending_responses (
    id INTEGER PRIMARY KEY,
    candidate_id INTEGER,
    channel VARCHAR (email/sms),
    incoming_message TEXT,
    generated_content TEXT,  -- AI's original response
    edited_content TEXT,     -- Human's edits (if any)
    status VARCHAR,          -- pending/approved/rejected/sent
    subject VARCHAR,         -- For emails
    recipient_email VARCHAR,
    recipient_phone VARCHAR,
    reviewed_by VARCHAR,     -- Recruiter name
    created_at TIMESTAMP,
    reviewed_at TIMESTAMP,
    sent_at TIMESTAMP
);
```

## API Endpoints Flow

```
GET /api/responses/pending
   │
   ├──► Returns list of all pending responses
   │
   └──► Recruiter selects one to review

PUT /api/responses/{id}/edit
   │
   ├──► Recruiter edits the content
   │
   └──► Updated in database

POST /api/responses/{id}/approve
   │
   ├──► Sends the response (edited or original)
   ├──► Logs conversation
   ├──► Updates status to "sent"
   │
   └──► Removes from pending queue

POST /api/responses/{id}/reject
   │
   ├──► Marks as rejected
   ├──► Does NOT send anything
   │
   └──► Removes from pending queue
```

## CLI Tool Interface

```
┌──────────────────────────────────────────────────────────┐
│  🏥 MetaSense Inc. - Interactive Response Manager        │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  📋 Pending Responses: 3                                 │
│                                                           │
│  [1] ID: 15 | EMAIL                                      │
│      Candidate: Maria Rodriguez                          │
│      Specialty: Emergency Room                           │
│      Created: 2025-12-16 14:23:10                        │
│                                                           │
│  [2] ID: 16 | SMS                                        │
│      Candidate: James Wilson                             │
│      Specialty: Physical Therapist                       │
│      Created: 2025-12-16 14:25:33                        │
│                                                           │
│  Enter number to review, 'R' to refresh, 'Q' to quit     │
│  Your choice: _                                          │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

## Summary

The agent is now **INTERACTIVE** because:

1. ✅ **Human approval required** before any response is sent
2. ✅ **Review interface** (CLI + API) for recruiters
3. ✅ **Edit capability** to personalize AI responses
4. ✅ **Approval workflow** with clear actions
5. ✅ **Audit trail** of who reviewed and approved

This transforms the system from a **fully automated** chatbot into a 
**human-assisted AI agent** that combines AI efficiency with human 
judgment and oversight.
