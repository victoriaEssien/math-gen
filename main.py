import google.generativeai as genai
import json
import sqlite3
from datetime import datetime
import warnings
import os
import re
from dotenv import load_dotenv

# Suppress warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ['GRPC_PYTHON_LOG_LEVEL'] = 'error'

load_dotenv()

api_key = os.getenv("API_KEY")
db_name = os.getenv("DB_NAME")

class InteractiveMathTutor:
    def __init__(self, api_key, db_name=db_name):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-pro")
        self.conn = sqlite3.connect(db_name)
        sqlite3.register_adapter(datetime, lambda x: x.isoformat())
        self.setup_database()
    
    def setup_database(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT,
            student_answer TEXT,
            correct_answer TEXT,
            is_correct BOOLEAN,
            attempt_date TIMESTAMP
        )
        ''')
        self.conn.commit()

    def normalize_answer(self, answer):
        """Normalize answer string for comparison (e.g., 'x=5' equals 'x = 5')"""
        # Remove spaces and convert to lowercase
        answer = re.sub(r'\s+', '', answer.lower())
        # Convert 'x=5' to 'x=5'
        answer = re.sub(r'(\w+)\s*=\s*(-?\d*\.?\d+)', r'\1=\2', answer)
        return answer

    def check_answer(self, student_answer, correct_answer):
        """Check if student's answer matches the correct answer"""
        return self.normalize_answer(student_answer) == self.normalize_answer(correct_answer)

    def generate_question(self, topic="algebra", difficulty="intermediate"):
        """Generate a math question"""
        prompt = f"""
        Create a {difficulty} level {topic} question.
        Format your response exactly like this example:
        {{
            "question": "Solve for x: 4x + 6 = 26",
            "answer": "x = 5",
            "solution_steps": [
                "1. Subtract 6 from both sides: 4x = 20",
                "2. Divide both sides by 4: x = 5"
            ]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)
        except Exception as e:
            print(f"Error generating question: {e}")
            return None

    def run_interactive_session(self):
        """Run an interactive math tutoring session"""
        print("\n=== Welcome to Interactive Math Tutor ===\n")
        
        while True:
            # Generate a new question
            question_data = self.generate_question()
            if not question_data:
                print("Error generating question. Please try again.")
                continue
            
            print("\nQuestion:", question_data['question'])
            
            # Get student's answer
            student_answer = input("\nYour answer (or 'hint' for a hint, 'quit' to exit): ")
            
            if student_answer.lower() == 'quit':
                print("\nThanks for practicing! Goodbye!")
                break
            
            if student_answer.lower() == 'hint':
                print("\nHint:", question_data['solution_steps'][0])
                student_answer = input("\nYour answer: ")
            
            # Check answer and store attempt
            is_correct = self.check_answer(student_answer, question_data['answer'])
            
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO student_attempts 
            (question_text, student_answer, correct_answer, is_correct, attempt_date)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                question_data['question'],
                student_answer,
                question_data['answer'],
                is_correct,
                datetime.now()
            ))
            self.conn.commit()
            
            if is_correct:
                print("\nCorrect! Well done! 🎉")
            else:
                print("\nNot quite right. Here's how to solve it:")
                for step in question_data['solution_steps']:
                    print(step)
                
                # Generate a similar question for practice
                print("\nLet's try a similar question for practice...")
            
            # Ask if they want to continue
            continue_practice = input("\nWould you like another question? (yes/no): ")
            if continue_practice.lower() != 'yes':
                print("\nThanks for practicing! Goodbye!")
                break

def main():
    tutor = InteractiveMathTutor(api_key=api_key)
    tutor.run_interactive_session()

if __name__ == "__main__":
    main()