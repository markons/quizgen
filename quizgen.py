"""
PL/I and Db2 Quiz System with AI-Generated Questions
=====================================================

System Architecture:
- GUI Layer: Tkinter-based user interface
- AI Integration: OpenAI API for question generation
- Data Layer: JSON-based storage for results
- Result Export: Text file generation with timestamp

Requirements:
- Python 3.7+
- tkinter (usually included with Python)
- openai library: pip install openai
- OpenAI API key (set as environment variable: OPENAI_API_KEY)

Usage:
1. Install OpenAI: pip install openai
2. Set your OpenAI API key as environment variable: OPENAI_API_KEY
3. Run the script: python quiz_system.py
4. Select topic and subtopic
5. Start the quiz
6. Answer questions and view results
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import random
from datetime import datetime
from typing import List, Dict, Tuple
import os

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: openai library not installed. Install with: pip install openai")


# AI Integration Module
class AIQuestionGenerator:
    """
    Handles AI-based question generation using OpenAI API.
    Generates domain-specific questions for PL/I and Db2.
    """

    def __init__(self):
        self.client = None
        self.api_available = self._initialize_openai()

    def _initialize_openai(self) -> bool:
        """Initialize OpenAI client with API key"""
        if not OPENAI_AVAILABLE:
            return False

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return False

        try:
            self.client = OpenAI(api_key=api_key)
            return True
        except Exception as e:
            print(f"Failed to initialize OpenAI: {e}")
            return False

    def generate_questions(self, topic: str, subtopic: str, count: int = 10, difficulty: str = "Intermediate") -> List[
        Dict]:
        """
        Generate quiz questions using OpenAI.

        Args:
            topic: Main topic (PL/I or Db2)
            subtopic: Specialized area within topic
            count: Number of questions to generate
            difficulty: Question difficulty level (Junior/Intermediate/Advanced/Senior)

        Returns:
            List of question dictionaries with options and correct answer
        """

        if not self.api_available:
            messagebox.showerror("API Error",
                                 "OpenAI API is not available.\n\n"
                                 "Please ensure:\n"
                                 "1. You have installed openai: pip install openai\n"
                                 "2. You have set OPENAI_API_KEY environment variable")
            return []

        try:
            return self._generate_with_openai(topic, subtopic, count, difficulty)
        except Exception as e:
            messagebox.showerror("Generation Error",
                                 f"Failed to generate questions from OpenAI:\n{str(e)}\n\n"
                                 "Please check your API key and internet connection.")
            return []

    def _generate_with_openai(self, topic: str, subtopic: str, count: int, difficulty: str = "Intermediate") -> List[
        Dict]:
        """Generate questions using OpenAI API"""

        # Map difficulty levels to specific instructions
        difficulty_instructions = {
            "Junior": "basic concepts, syntax, and fundamental principles. Questions should test foundational knowledge.",
            "Intermediate": "practical applications, common patterns, and moderately complex scenarios. Questions should test working knowledge.",
            "Advanced": "complex scenarios, optimization, edge cases, and deep technical understanding. Questions should test expert-level knowledge.",
            "Senior": "architectural decisions, performance tuning, best practices, and advanced troubleshooting. Questions should test mastery-level expertise."
        }

        difficulty_desc = difficulty_instructions.get(difficulty, difficulty_instructions["Intermediate"])

        prompt = f"""Generate {count} multiple-choice quiz questions about {topic} - {subtopic}.

Difficulty Level: {difficulty}
Focus on {difficulty_desc}

Requirements:
1. Each question must be technical and domain-specific
2. Each question must have exactly 4 answer options
3. Only one option must be correct
4. All questions should be at the {difficulty} level
5. Questions should test practical knowledge and understanding appropriate for {difficulty} developers

IMPORTANT: Return ONLY a JSON object with a "questions" array. No other text or markdown.

Return the questions in EXACTLY this JSON format:
{{
  "questions": [
    {{
      "question": "Question text here?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct": 0,
      "difficulty": "{difficulty.lower()}"
    }}
  ]
}}

The "correct" field must be an integer (0, 1, 2, or 3) indicating the index of the correct answer.

Generate exactly {count} questions now in the format above."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4 for better quality questions
                # messages=[
                #     {
                #         "role": "system",
                #         "content": (
                #             f"You are an expert in IBM Enterprise PL/I for z/OS and Db2 for z/OS SQL. "
                #             f"Generate high-quality {difficulty}-level technical quiz questions suitable for mainframe developers. "
                #             "All PL/I code must strictly follow IBM Enterprise PL/I syntax and semantics as defined in the IBM Language Reference and Programming Guide. "
                #             "All SQL must follow Db2 for z/OS syntax and EXEC SQL rules. "
                #             "Avoid all non-IBM PL/I dialects. "
                #             "Output only the questions."
                #         )
                #     },
                #     {
                #         "role": "user",
                #         "content": prompt
                #     }
                # ],
                # python
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are an expert in IBM Enterprise PL/I for z/OS and Db2 for z/OS SQL. "
                            f"Generate high-quality {difficulty}-level technical quiz questions suitable for mainframe developers. "
                            "Follow these instructions EXACTLY and output ONLY the required JSON object (no prose, no markdown, no extra fields).\n\n"
                            "OUTPUT SCHEMA (must be followed exactly):\n"
                            "{{\n"
                            "  \"questions\": [\n"
                            "    {{\n"
                            "      \"question\": \"string\",\n"
                            "      \"options\": [\"string\",\"string\",\"string\",\"string\"],\n"
                            "      \"correct\": 0,                      // integer 0..3 index into options\n"
                            "      \"explanation\": \"string <=30 words\",\n"
                            "      \"pli_code\": \"string or empty\",   // raw PL/I snippet or empty string\n"
                            "      \"compiles\": true|false,            // true if pli_code guaranteed to compile in IBM Enterprise PL/I for z/OS\n"
                            "      \"compiler_notes\": \"one-line justification referencing IBM Enterprise PL/I rule or reason for non-compilation\"\n"
                            "    }}\n"
                            "  ]\n"
                            "}}\n\n"
                            "REQUIREMENTS:\n"
                            "1) Return EXACTLY one JSON object that conforms to the schema above. No additional text.\n"
                            "2) Produce exactly the requested number of questions. If you cannot produce that many valid items, return\n"
                            "   {{\"questions\": [], \"error\": \"explain briefly why\"}} and nothing else.\n"
                            "3) Each question must have exactly 4 non-empty options and exactly one correct index (0..3).\n"
                            "4) \"explanation\" must be <=30 words and state why the correct option is correct.\n"
                            "5) If including PL/I code in \"pli_code\": the code MUST conform to IBM Enterprise PL/I for z/OS. If uncertain set \"pli_code\":\"\" and \"compiles\": false and explain why in \"compiler_notes\".\n"
                            "6) For any SQL examples, follow Db2 for z/OS syntax and use EXEC SQL where appropriate; if uncertain, omit SQL or mark as non-compiling.\n"
                            "7) Do NOT invent PL/I features, non-IBM dialects, or unsupported extensions. Prioritize correctness over variety.\n"
                            "8) Be conservative: if not 100% certain about PL/I compilation, omit the PL/I snippet and set \"compiles\": false.\n"
                            "9) Ensure the returned JSON is parseable (no trailing comments or extra text) and escaped properly.\n\n"
                            "If any requirement cannot be satisfied for a generated question, set \"pli_code\":\"\", \"compiles\": false, and provide a concise \"compiler_notes\" explaining the uncertainty."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

            temperature=0.8,  # Slightly higher for variety
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content

            # Parse the JSON response
            try:
                data = json.loads(content)
                # Handle both direct array and object with array
                if isinstance(data, list):
                    questions = data
                elif isinstance(data, dict) and 'questions' in data:
                    questions = data['questions']
                else:
                    # Try to find the first list in the data
                    questions = next((v for v in data.values() if isinstance(v, list)), [])

                # Validate and process questions
                validated_questions = []
                for i, q in enumerate(questions):
                    try:
                        if self._validate_question(q):
                            # Ensure correct is an integer
                            if isinstance(q['correct'], str):
                                q['correct'] = int(q['correct'])

                            # Randomize options
                            correct_answer = q['options'][q['correct']]
                            random.shuffle(q['options'])
                            q['correct'] = q['options'].index(correct_answer)
                            validated_questions.append(q)
                        else:
                            print(f"Question {i + 1} failed validation: {q}")
                    except Exception as e:
                        print(f"Error processing question {i + 1}: {e}")
                        print(f"Question data: {q}")
                        continue

                if not validated_questions:
                    raise ValueError(f"No valid questions generated. Raw response: {content[:500]}")

                if len(validated_questions) < count * 0.5:  # At least 50% valid
                    print(f"Warning: Only {len(validated_questions)} out of {count} questions are valid")

                return validated_questions[:count]

            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse OpenAI response as JSON: {e}\nResponse: {content[:500]}")

        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    def _validate_question(self, question: Dict) -> bool:
        """Validate a question has all required fields"""
        try:
            # Check required fields exist
            required_fields = ['question', 'options', 'correct']
            if not all(field in question for field in required_fields):
                print(f"Missing required fields. Has: {question.keys()}")
                return False

            # Validate question text
            if not isinstance(question['question'], str) or not question['question'].strip():
                print(f"Invalid question text: {question.get('question')}")
                return False

            # Validate options
            if not isinstance(question['options'], list):
                print(f"Options is not a list: {type(question['options'])}")
                return False

            if len(question['options']) != 4:
                print(f"Options count is {len(question['options'])}, expected 4")
                return False

            # Check all options are non-empty strings
            for opt in question['options']:
                if not isinstance(opt, str) or not opt.strip():
                    print(f"Invalid option: {opt}")
                    return False

            # Validate correct answer index
            correct = question['correct']
            if isinstance(correct, str):
                try:
                    correct = int(correct)
                except ValueError:
                    print(f"Cannot convert correct to int: {correct}")
                    return False

            if not isinstance(correct, int):
                print(f"Correct is not an integer: {type(correct)}")
                return False

            if correct not in range(4):
                print(f"Correct index {correct} is out of range [0-3]")
                return False

            return True

        except Exception as e:
            print(f"Validation exception: {e}")
            return False


# Database/Storage Module
class ResultStorage:
    """
    Handles storage and retrieval of quiz results.
    Stores results in JSON format and exports to text files.
    """

    def __init__(self):
        self.results_dir = 'quiz_results'
        self._ensure_directory()

    def _ensure_directory(self):
        """Create results directory if it doesn't exist"""
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

    def save_result(self, result_data: Dict) -> str:
        """
        Save quiz result to file.

        Args:
            result_data: Dictionary containing quiz results

        Returns:
            Filename of saved result
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Create abbreviated student name (initials or shortened version)
        student_name = result_data.get('student_name', 'unknown')
        abbreviated_name = self._abbreviate_name(student_name)

        filename = f'quiz_result_{abbreviated_name}_{timestamp}.txt'
        filepath = os.path.join(self.results_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self._format_result(result_data))

        # Also save JSON version for data analysis
        json_filepath = filepath.replace('.txt', '.json')
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2)

        return filepath

    def _abbreviate_name(self, name: str) -> str:
        """
        Create abbreviated version of student name.
        Examples:
            "John Doe" -> "JDoe"
            "Jane Smith Johnson" -> "JSJohnson"
            "Michael" -> "Michael"
        """
        if not name:
            return "unknown"

        # Clean the name
        name = name.strip()
        parts = name.split()

        if len(parts) == 1:
            # Single name: use as is (max 10 chars)
            return parts[0][:10]
        elif len(parts) == 2:
            # First Last: use first initial + last name
            return f"{parts[0][0]}{parts[1]}"
        else:
            # Multiple names: use initials except last name
            initials = ''.join([p[0] for p in parts[:-1]])
            return f"{initials}{parts[-1]}"

        # Remove any special characters and limit length
        abbreviated = ''.join(c for c in abbreviated if c.isalnum())
        return abbreviated[:15]

    def _format_result(self, data: Dict) -> str:
        """Format result data as readable text"""
        output = []
        output.append("=" * 60)
        output.append("QUIZ RESULT REPORT")
        output.append("=" * 60)
        output.append(f"\nStudent Name: {data.get('student_name', 'N/A')}")
        output.append(f"Date/Time: {data['timestamp']}")
        output.append(f"Topic: {data['topic']}")
        output.append(f"Subtopic: {data['subtopic']}")
        output.append(f"Difficulty Level: {data['difficulty']}")
        output.append(f"\nTotal Questions: {data['total_questions']}")
        output.append(f"Correct Answers: {data['correct_answers']}")
        output.append(f"Incorrect Answers: {data['incorrect_answers']}")
        output.append(f"Score: {data['percentage']:.1f}%")
        output.append(f"\nGrade: {data['grade']}")
        output.append("\n" + "-" * 60)
        output.append("DETAILED ANSWERS")
        output.append("-" * 60)

        for i, qa in enumerate(data['questions'], 1):
            output.append(f"\nQuestion {i}: {qa['question']}")
            output.append(f"Your Answer: {qa['user_answer']}")
            output.append(f"Correct Answer: {qa['correct_answer']}")
            output.append(f"Result: {'✓ CORRECT' if qa['is_correct'] else '✗ INCORRECT'}")

        output.append("\n" + "=" * 60)
        output.append("END OF REPORT")
        output.append("=" * 60)

        return '\n'.join(output)


# GUI Components
class QuizGUI:
    """
    Main GUI application for the quiz system.
    Handles user interaction, question display, and result presentation.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("PL/I and Db2 Quiz System")
        self.root.geometry("800x600")

        # Configure grid weight for responsive design
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Initialize components
        self.ai_generator = AIQuestionGenerator()
        self.storage = ResultStorage()

        # Quiz state
        self.questions = []
        self.current_question = 0
        self.user_answers = []
        self.selected_topic = tk.StringVar(value='PL/I')
        self.selected_subtopic = tk.StringVar()
        self.selected_difficulty = tk.StringVar(value='Intermediate')
        self.student_name = tk.StringVar()

        # Subtopic mappings
        self.subtopics = {
            'PL/I': ['Data Types', 'Structures', 'I/O Operations', 'Conditions', 'Built-in Functions'],
            'Db2': ['SQL DML', 'SQL DDL', 'Indexing', 'Joins', 'Constraints']
        }

        # Create UI
        self.create_widgets()
        self.show_setup_screen()

    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

    def show_setup_screen(self):
        """Display topic and subtopic selection screen"""
        self.clear_main_frame()

        setup_frame = ttk.Frame(self.main_frame)
        setup_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title = ttk.Label(setup_frame, text="Quiz Setup", font=('Arial', 20, 'bold'))
        title.grid(row=0, column=0, columnspan=2, pady=20)

        # Student name input
        ttk.Label(setup_frame, text="Student Name:", font=('Arial', 12)).grid(row=1, column=0, sticky=tk.W, pady=10)

        name_entry = ttk.Entry(setup_frame, textvariable=self.student_name, width=32)
        name_entry.grid(row=1, column=1, sticky=tk.W, pady=10)
        name_entry.focus()

        # Topic selection
        ttk.Label(setup_frame, text="Select Topic:", font=('Arial', 12)).grid(row=2, column=0, sticky=tk.W, pady=10)

        topic_frame = ttk.Frame(setup_frame)
        topic_frame.grid(row=2, column=1, sticky=tk.W, pady=10)

        ttk.Radiobutton(topic_frame, text="PL/I", variable=self.selected_topic,
                        value="PL/I", command=self.update_subtopics).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(topic_frame, text="Db2", variable=self.selected_topic,
                        value="Db2", command=self.update_subtopics).pack(side=tk.LEFT, padx=10)

        # Subtopic selection
        ttk.Label(setup_frame, text="Select Subtopic:", font=('Arial', 12)).grid(row=3, column=0, sticky=tk.W, pady=10)

        self.subtopic_combo = ttk.Combobox(setup_frame, textvariable=self.selected_subtopic,
                                           width=30, state='readonly')
        self.subtopic_combo.grid(row=3, column=1, sticky=tk.W, pady=10)
        self.update_subtopics()

        # Difficulty level selection
        ttk.Label(setup_frame, text="Question Difficulty:", font=('Arial', 12)).grid(row=4, column=0, sticky=tk.W,
                                                                                     pady=10)

        difficulty_frame = ttk.Frame(setup_frame)
        difficulty_frame.grid(row=4, column=1, sticky=tk.W, pady=10)

        difficulty_combo = ttk.Combobox(difficulty_frame, textvariable=self.selected_difficulty,
                                        values=['Junior', 'Intermediate', 'Advanced', 'Senior'],
                                        width=15, state='readonly')
        difficulty_combo.pack(side=tk.LEFT)

        # Info button for difficulty levels
        info_btn = ttk.Button(difficulty_frame, text="?", width=3,
                              command=self.show_difficulty_info)
        info_btn.pack(side=tk.LEFT, padx=5)

        # Number of questions
        ttk.Label(setup_frame, text="Number of Questions:", font=('Arial', 12)).grid(row=5, column=0, sticky=tk.W,
                                                                                     pady=10)

        self.num_questions = tk.IntVar(value=10)
        question_spin = ttk.Spinbox(setup_frame, from_=5, to=20, textvariable=self.num_questions, width=10)
        question_spin.grid(row=5, column=1, sticky=tk.W, pady=10)

        # Start button
        start_btn = ttk.Button(setup_frame, text="Start Quiz", command=self.start_quiz,
                               style='Accent.TButton')
        start_btn.grid(row=6, column=0, columnspan=2, pady=30)

        # API status
        api_status = "OpenAI API: " + (
            "Connected" if self.ai_generator.api_available else "Not Available - Check API Key")
        status_label = ttk.Label(setup_frame, text=api_status,
                                 foreground='green' if self.ai_generator.api_available else 'red')
        status_label.grid(row=7, column=0, columnspan=2)

        # Keyboard navigation
        self.root.bind('<Return>', lambda e: self.start_quiz())

    def update_subtopics(self):
        """Update subtopic dropdown based on selected topic"""
        topic = self.selected_topic.get()
        subtopics = self.subtopics.get(topic, [])
        self.subtopic_combo['values'] = subtopics
        if subtopics:
            self.selected_subtopic.set(subtopics[0])

    def show_difficulty_info(self):
        """Show information about difficulty levels"""
        info_text = """Question Difficulty Levels:

🟢 Junior
   • Basic concepts and syntax
   • Fundamental principles
   • Entry-level knowledge

🟡 Intermediate
   • Practical applications
   • Common patterns
   • Working knowledge

🟠 Advanced
   • Complex scenarios
   • Optimization techniques
   • Deep technical understanding

🔴 Senior
   • Architectural decisions
   • Performance tuning
   • Best practices & troubleshooting
   • Expert-level mastery"""

        messagebox.showinfo("Difficulty Levels", info_text)

    def start_quiz(self):
        """Initialize and start the quiz"""
        student_name = self.student_name.get().strip()
        topic = self.selected_topic.get()
        subtopic = self.selected_subtopic.get()
        difficulty = self.selected_difficulty.get()
        count = self.num_questions.get()

        # Validate student name
        if not student_name:
            messagebox.showwarning("Name Required", "Please enter your name.")
            return

        if not subtopic:
            messagebox.showwarning("Selection Required", "Please select a subtopic.")
            return

        if not self.ai_generator.api_available:
            messagebox.showerror("API Not Available",
                                 "OpenAI API is not available.\n\n"
                                 "Please ensure:\n"
                                 "1. You have installed openai: pip install openai\n"
                                 "2. You have set OPENAI_API_KEY environment variable\n\n"
                                 "On Windows: set OPENAI_API_KEY=your-key-here\n"
                                 "On Linux/Mac: export OPENAI_API_KEY=your-key-here")
            return

        # Show loading message
        loading = messagebox.showinfo("Generating Questions",
                                      f"Generating {count} {difficulty}-level questions about {topic} - {subtopic}...\n\n"
                                      "This may take a moment. Please wait.")

        # Generate questions
        try:
            self.root.config(cursor="watch")
            self.root.update()

            self.questions = self.ai_generator.generate_questions(topic, subtopic, count, difficulty)

            self.root.config(cursor="")

            if not self.questions:
                messagebox.showerror("Error", "No questions were generated. Please try again.")
                return

            self.current_question = 0
            self.user_answers = []
            self.show_question_screen()
        except Exception as e:
            self.root.config(cursor="")
            messagebox.showerror("Error", f"Failed to generate questions: {str(e)}")

    def show_question_screen(self):
        """Display current question"""
        self.clear_main_frame()

        if self.current_question >= len(self.questions):
            self.show_results_screen()
            return

        question_frame = ttk.Frame(self.main_frame)
        question_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=20, pady=20)

        q = self.questions[self.current_question]

        # Progress
        progress_text = f"Question {self.current_question + 1} of {len(self.questions)}"
        ttk.Label(question_frame, text=progress_text, font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W)

        # Question text
        question_label = ttk.Label(question_frame, text=q['question'],
                                   font=('Arial', 14, 'bold'), wraplength=700)
        question_label.grid(row=1, column=0, pady=20, sticky=tk.W)

        # Answer options
        self.selected_answer = tk.IntVar(value=-1)

        for i, option in enumerate(q['options']):
            rb = ttk.Radiobutton(question_frame, text=option, variable=self.selected_answer,
                                 value=i, command=lambda: self.next_btn.config(state='normal'))
            rb.grid(row=i + 2, column=0, sticky=tk.W, pady=5, padx=20)

        # Navigation buttons
        btn_frame = ttk.Frame(question_frame)
        btn_frame.grid(row=len(q['options']) + 3, column=0, pady=20)

        if self.current_question > 0:
            prev_btn = ttk.Button(btn_frame, text="← Previous", command=self.previous_question)
            prev_btn.pack(side=tk.LEFT, padx=5)

        self.next_btn = ttk.Button(btn_frame,
                                   text="Next →" if self.current_question < len(self.questions) - 1 else "Finish",
                                   command=self.next_question, state='disabled')
        self.next_btn.pack(side=tk.LEFT, padx=5)

        # Keyboard navigation
        self.root.bind('<Return>', lambda e: self.next_question() if self.selected_answer.get() != -1 else None)
        self.root.bind('<Left>', lambda e: self.previous_question() if self.current_question > 0 else None)
        self.root.bind('<Right>', lambda e: self.next_question() if self.selected_answer.get() != -1 else None)
        for i in range(1, 5):
            self.root.bind(str(i), lambda e, idx=i - 1: self.select_option(idx))

    def select_option(self, index):
        """Select option via keyboard"""
        if index < len(self.questions[self.current_question]['options']):
            self.selected_answer.set(index)
            self.next_btn.config(state='normal')

    def next_question(self):
        """Move to next question"""
        if self.selected_answer.get() == -1:
            messagebox.showwarning("Selection Required", "Please select an answer.")
            return

        # Store answer
        if self.current_question >= len(self.user_answers):
            self.user_answers.append(self.selected_answer.get())
        else:
            self.user_answers[self.current_question] = self.selected_answer.get()

        self.current_question += 1

        if self.current_question < len(self.questions):
            self.show_question_screen()
        else:
            self.show_results_screen()

    def previous_question(self):
        """Move to previous question"""
        if self.current_question > 0:
            self.current_question -= 1
            self.show_question_screen()
            if self.current_question < len(self.user_answers):
                self.selected_answer.set(self.user_answers[self.current_question])
                self.next_btn.config(state='normal')

    def show_results_screen(self):
        """Display quiz results"""
        self.clear_main_frame()

        results_frame = ttk.Frame(self.main_frame)
        results_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.grid_rowconfigure(1, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        # Calculate results
        correct = sum(1 for i, ans in enumerate(self.user_answers)
                      if ans == self.questions[i]['correct'])
        total = len(self.questions)
        percentage = (correct / total) * 100

        # Determine grade
        if percentage >= 90:
            grade = "A - Excellent"
        elif percentage >= 80:
            grade = "B - Very Good"
        elif percentage >= 70:
            grade = "C - Good"
        elif percentage >= 60:
            grade = "D - Passing"
        else:
            grade = "F - Needs Improvement"

        # Title
        title = ttk.Label(results_frame, text="Quiz Results", font=('Arial', 20, 'bold'))
        title.grid(row=0, column=0, pady=20)

        # Summary
        summary_frame = ttk.Frame(results_frame)
        summary_frame.grid(row=1, column=0, pady=10)

        ttk.Label(summary_frame, text=f"Student: {self.student_name.get()}",
                  font=('Arial', 12, 'bold')).pack(pady=5)
        ttk.Label(summary_frame, text=f"Topic: {self.selected_topic.get()}",
                  font=('Arial', 12)).pack(pady=5)
        ttk.Label(summary_frame, text=f"Subtopic: {self.selected_subtopic.get()}",
                  font=('Arial', 12)).pack(pady=5)
        ttk.Label(summary_frame, text=f"Difficulty: {self.selected_difficulty.get()}",
                  font=('Arial', 12)).pack(pady=5)
        ttk.Label(summary_frame, text=f"Score: {correct}/{total} ({percentage:.1f}%)",
                  font=('Arial', 14, 'bold')).pack(pady=10)
        ttk.Label(summary_frame, text=f"Grade: {grade}",
                  font=('Arial', 14), foreground='green' if percentage >= 70 else 'red').pack(pady=5)

        # Detailed results in scrolled text
        details_label = ttk.Label(results_frame, text="Detailed Results:", font=('Arial', 12, 'bold'))
        details_label.grid(row=2, column=0, pady=(20, 5), sticky=tk.W)

        details_text = scrolledtext.ScrolledText(results_frame, width=80, height=15, wrap=tk.WORD)
        details_text.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        for i, (q, ans) in enumerate(zip(self.questions, self.user_answers)):
            is_correct = ans == q['correct']
            details_text.insert(tk.END, f"Q{i + 1}: {q['question']}\n")
            details_text.insert(tk.END, f"Your Answer: {q['options'][ans]}\n")
            details_text.insert(tk.END, f"Correct Answer: {q['options'][q['correct']]}\n")
            details_text.insert(tk.END, f"{'✓ CORRECT' if is_correct else '✗ INCORRECT'}\n\n")

        details_text.config(state='disabled')

        # Prepare result data
        result_data = {
            'student_name': self.student_name.get(),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'topic': self.selected_topic.get(),
            'subtopic': self.selected_subtopic.get(),
            'difficulty': self.selected_difficulty.get(),
            'total_questions': total,
            'correct_answers': correct,
            'incorrect_answers': total - correct,
            'percentage': percentage,
            'grade': grade,
            'questions': [
                {
                    'question': q['question'],
                    'user_answer': q['options'][ans],
                    'correct_answer': q['options'][q['correct']],
                    'is_correct': ans == q['correct']
                }
                for q, ans in zip(self.questions, self.user_answers)
            ]
        }

        # Buttons
        btn_frame = ttk.Frame(results_frame)
        btn_frame.grid(row=4, column=0, pady=20)

        save_btn = ttk.Button(btn_frame, text="Save Results",
                              command=lambda: self.save_results(result_data))
        save_btn.pack(side=tk.LEFT, padx=5)

        restart_btn = ttk.Button(btn_frame, text="New Quiz", command=self.show_setup_screen)
        restart_btn.pack(side=tk.LEFT, padx=5)

        exit_btn = ttk.Button(btn_frame, text="Exit", command=self.root.quit)
        exit_btn.pack(side=tk.LEFT, padx=5)

    def save_results(self, result_data: Dict):
        """Save quiz results to file"""
        try:
            filepath = self.storage.save_result(result_data)
            messagebox.showinfo("Success", f"Results saved to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save results: {str(e)}")

    def clear_main_frame(self):
        """Clear all widgets from main frame"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        # Unbind all keyboard shortcuts
        self.root.unbind('<Return>')
        self.root.unbind('<Left>')
        self.root.unbind('<Right>')
        for i in range(1, 5):
            self.root.unbind(str(i))


def main():
    """Main application entry point"""
    root = tk.Tk()

    # Configure style
    style = ttk.Style()
    style.theme_use('clam')

    app = QuizGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()