# database.py
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional

class ConversationDB:
    def __init__(self, db_path="recruitment_agent.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Candidates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE,
                phone TEXT,
                first_name TEXT,
                last_name TEXT,
                specialty TEXT,
                current_job TEXT,
                status TEXT DEFAULT 'new',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY,
                candidate_id INTEGER,
                channel TEXT,  # 'email' or 'sms'
                message_type TEXT,  # 'outbound' or 'inbound'
                content TEXT,
                message_id TEXT,  # For email threading or SMS ID
                parent_message_id INTEGER,  # For conversation threading
                sentiment TEXT,
                needs_follow_up BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidates (id)
            )
        ''')
        
        # Campaign responses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaign_responses (
                id INTEGER PRIMARY KEY,
                candidate_id INTEGER,
                campaign_type TEXT,
                initial_message TEXT,
                response_received BOOLEAN DEFAULT 0,
                response_content TEXT,
                response_time DATETIME,
                converted BOOLEAN DEFAULT 0,
                FOREIGN KEY (candidate_id) REFERENCES candidates (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_candidate(self, candidate_data: Dict) -> int:
        """Add candidate to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO candidates 
            (email, phone, first_name, last_name, specialty, current_job, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            candidate_data.get('EMAIL'),
            candidate_data.get('MOBILE PHONE'),
            candidate_data.get('FIRST NAME'),
            candidate_data.get('LAST NAME'),
            candidate_data.get('SPECIALTY'),
            candidate_data.get('CURRENT JOB'),
            'new'
        ))
        
        candidate_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return candidate_id
    
    def log_conversation(self, candidate_id: int, channel: str, message_type: str, 
                        content: str, message_id: str = None, parent_message_id: int = None):
        """Log a conversation message"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations 
            (candidate_id, channel, message_type, content, message_id, parent_message_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (candidate_id, channel, message_type, content, message_id, parent_message_id))
        
        conn.commit()
        conn.close()
    
    def get_conversation_history(self, candidate_id: int, limit: int = 10) -> List[Dict]:
        """Get conversation history for a candidate"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT channel, message_type, content, created_at
            FROM conversations 
            WHERE candidate_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (candidate_id, limit))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'channel': row[0],
                'message_type': row[1],
                'content': row[2],
                'timestamp': row[3]
            })
        
        conn.close()
        return history[::-1]  # Return in chronological order
    
    def update_candidate_status(self, candidate_id: int, status: str):
        """Update candidate status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE candidates SET status = ? WHERE id = ?
        ''', (status, candidate_id))
        
        conn.commit()
        conn.close()