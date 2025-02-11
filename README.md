# MathGen (AI-Generated Question Creation)

An interactive math tutoring application that uses Google's Gemini Pro AI model to generate personalized math questions and provide detailed explanations. The system features adaptive question generation, immediate feedback, and performance tracking.

## Technology Stack

### Backend
- **FastAPI**: High-performance web framework for building APIs
- **SQLite**: Lightweight, serverless database for storing questions and student attempts
- **Google Gemini Pro**: AI model for generating questions and explanations
- **Pydantic**: Data validation using Python type annotations

### Frontend
- **React**: UI library for building the user interface
- **Shadcn/UI**: Component library for consistent design
- **Tailwind CSS**: Utility-first CSS framework for styling

## Database Design

The application uses SQLite with two main tables:

### Questions Table
```sql
CREATE TABLE questions (
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
```

### Student Attempts Table
```sql
CREATE TABLE student_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER,
    selected_answer TEXT,
    is_correct BOOLEAN,
    attempt_date TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions (id)
)
```

## Question Generation Process

1. **Topic and Difficulty Selection**
   - Users select a mathematical topic (Algebra, Geometry, Trigonometry, Calculus, Statistics)
   - Users choose difficulty level (Beginner, Intermediate, Advanced)

2. **AI Question Generation**
   - The system sends a structured prompt to Gemini Pro
   - The AI generates:
     - Question text
     - Multiple choice options
     - Step-by-step solution
     - Detailed explanation
   - Response is validated for correct format and completeness

3. **Storage and Retrieval**
   - Generated questions are stored in SQLite database
   - Each question includes metadata for tracking and analysis
   - Student attempts are recorded for performance analysis

## Adaptive Learning Features

When a student answers incorrectly:
1. The system records the incorrect attempt
2. Provides immediate feedback with detailed explanations
3. Shows step-by-step solution process
4. Generates a new question based on the same topic and difficulty
5. Tracks performance statistics for analysis

## API Endpoints

### POST /questions
Generates a new math question
```json
{
  "topic": "algebra",
  "difficulty": "intermediate"
}
```

### POST /submit
Submits an answer and receives feedback
```json
{
  "question_id": 1,
  "selected_answer": "x = 5"
}
```

## Setup Instructions

1. Clone the repository
```bash
git clone https://github.com/victoriaEssien/math-gen.git
cd math-gen
```

2. Install backend dependencies
```bash
pip install -r requirements.txt
```

3. Set up environment variables
```bash
# .env file
API_KEY=your_gemini_api_key
ALLOWED_ORIGIN=http://localhost:5173
```

4. Install frontend dependencies
```bash
cd frontend
npm install
```

5. Start the backend server
```bash
uvicorn main:app --reload
```
or
```bash
python main.py
```

6. Start the frontend development server
```bash
npm run dev
```

## Environment Variables

- `API_KEY`: Google Gemini Pro API key
- `ALLOWED_ORIGIN`: Frontend application URL for CORS
- `VITE_BASE_URL`: Base url for the api e.g http://localhost:3000
  

## Contact

Discord: @vic_essien
