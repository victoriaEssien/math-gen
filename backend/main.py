from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import google.generativeai as genai
import json
import sqlite3
import warnings
import os
import re
from dotenv import load_dotenv
from enum import Enum
from contextlib import contextmanager

# Load environment variables
load_dotenv()
api_key = os.getenv("API_KEY")
db_name = os.getenv("DB_NAME")

if not api_key or not db_name:
    raise ValueError("Missing required environment variables: API_KEY and/or DB_NAME")

# Configure warnings and environment
warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ['GRPC_PYTHON_LOG_LEVEL'] = 'error'

class MathTopic(str, Enum):
    ALGEBRA = "algebra"
    GEOMETRY = "geometry"
    TRIGONOMETRY = "trigonometry"
    CALCULUS = "calculus"
    STATISTICS = "statistics"

class Difficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class QuestionRequest(BaseModel):
    topic: MathTopic
    difficulty: Difficulty

class Answer(BaseModel):
    text: str
    is_correct: bool

class Question(BaseModel):
    id: int
    question_text: str
    options: List[Answer]
    solution_steps: List[str]
    explanation: str

class SubmissionRequest(BaseModel):
    question_id: int
    selected_answer: str

class SubmissionResponse(BaseModel):
    is_correct: bool
    explanation: str
    solution_steps: List[str]
    performance_stats: dict

class DatabaseError(Exception):
    pass

class MathTutorAPI:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key is required")
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-pro")
        self.setup_database()

    @contextmanager
    def get_db_connection(self):
        conn = sqlite3.connect(db_name)
        sqlite3.register_adapter(datetime, lambda x: x.isoformat())
        try:
            yield conn
        finally:
            conn.close()

    def setup_database(self):
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT,
                    difficulty TEXT,
                    question_text TEXT,
                    correct_answer TEXT,
                    options TEXT,
                    solution_steps TEXT,
                    explanation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS student_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER,
                    selected_answer TEXT,
                    is_correct BOOLEAN,
                    attempt_date TIMESTAMP,
                    FOREIGN KEY (question_id) REFERENCES questions (id)
                )
                ''')
                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to setup database: {str(e)}")

    def validate_question_response(self, question_data: dict) -> bool:
        required_fields = ['question', 'options', 'solution_steps', 'explanation']
        if not all(field in question_data for field in required_fields):
            return False
        
        if not isinstance(question_data['options'], list) or len(question_data['options']) < 2:
            return False
            
        correct_answers = sum(1 for opt in question_data['options'] if opt.get('is_correct'))
        if correct_answers != 1:
            return False
            
        return True

    def generate_question(self, topic: MathTopic, difficulty: Difficulty) -> Question:
        prompt = f"""
        Create a {difficulty.value} level {topic.value} question with multiple choice options.
        Format your response exactly like this example:
        {{
            "question": "Solve for x: 4x + 6 = 26",
            "options": [
                {{"text": "x = 5", "is_correct": true}},
                {{"text": "x = 4", "is_correct": false}},
                {{"text": "x = 6", "is_correct": false}},
                {{"text": "x = 7", "is_correct": false}}
            ],
            "solution_steps": [
                "1. Subtract 6 from both sides: 4x = 20",
                "2. Divide both sides by 4: x = 5"
            ],
            "explanation": "This is a linear equation. We isolate x by first moving all non-x terms to the right side, then dividing both sides by the coefficient of x."
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            if not response.text:
                raise ValueError("Empty response from AI model")

            response_text = response.text
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("Invalid JSON format in response")
                
            json_str = response_text[start_idx:end_idx]
            question_data = json.loads(json_str)
            
            if not self.validate_question_response(question_data):
                raise ValueError("Invalid question format in response")

            # Store question in database
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO questions 
                (topic, difficulty, question_text, correct_answer, options, solution_steps, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    topic.value,
                    difficulty.value,
                    question_data['question'],
                    next(opt['text'] for opt in question_data['options'] if opt['is_correct']),
                    json.dumps(question_data['options']),
                    json.dumps(question_data['solution_steps']),
                    question_data['explanation']
                ))
                question_id = cursor.lastrowid
                conn.commit()
            
            return Question(
                id=question_id,
                question_text=question_data['question'],
                options=question_data['options'],
                solution_steps=question_data['solution_steps'],
                explanation=question_data['explanation']
            )
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Invalid response format: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating question: {str(e)}")

    def submit_answer(self, question_id: int, selected_answer: str) -> SubmissionResponse:
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get question details
                cursor.execute('''
                SELECT correct_answer, solution_steps, explanation 
                FROM questions 
                WHERE id = ?
                ''', (question_id,))
                question_data = cursor.fetchone()
                
                if not question_data:
                    raise HTTPException(status_code=404, detail="Question not found")
                
                correct_answer, solution_steps, explanation = question_data
                is_correct = selected_answer == correct_answer
                
                # Store attempt
                cursor.execute('''
                INSERT INTO student_attempts 
                (question_id, selected_answer, is_correct, attempt_date)
                VALUES (?, ?, ?, ?)
                ''', (question_id, selected_answer, is_correct, datetime.now()))
                
                # Calculate performance stats
                cursor.execute('''
                SELECT 
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_attempts
                FROM student_attempts 
                WHERE question_id = ?
                ''', (question_id,))
                stats = cursor.fetchone()
                
                conn.commit()
                
                performance_stats = {
                    "total_attempts": stats[0],
                    "correct_attempts": stats[1],
                    "success_rate": round((stats[1] / stats[0]) * 100, 2) if stats[0] > 0 else 0
                }
                
                return SubmissionResponse(
                    is_correct=is_correct,
                    explanation=explanation,
                    solution_steps=json.loads(solution_steps),
                    performance_stats=performance_stats
                )
        except sqlite3.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Create FastAPI app
app = FastAPI(title="Math Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize tutor after FastAPI app creation
tutor = MathTutorAPI(api_key=api_key)

@app.post("/questions", response_model=Question)
async def create_question(request: QuestionRequest):
    return tutor.generate_question(request.topic, request.difficulty)

@app.post("/submit", response_model=SubmissionResponse)
async def submit_answer(submission: SubmissionRequest):
    return tutor.submit_answer(submission.question_id, submission.selected_answer)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)