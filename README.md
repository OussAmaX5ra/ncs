# 📚 StudyMateAI

**StudyMateAI** is an AI-powered educational assistant designed to help students organize their studies, understand code, summarize academic materials, and manage deadlines—all within one modular and intuitive platform.

---

## 🚀 Features

### 🎯 Roadmap Inventor
- Converts syllabus, slides, or notes into personalized visual learning plans.
- Built using **RAG (Retrieval-Augmented Generation)** with SentenceTransformers and ChromaDB.

### 🤖 Code With Me
- Accepts Python code snippets and outputs:
  - Detailed explanations
  - Bug detection
  - Suggestions for improvement
- Powered by a **fine-tuned model** specialized in Python and web frameworks.

### 🧠 Smart Summarizer
- Extracts key insights from:
  - PDFs
  - Word documents
  - Raw text
- Supports both **extractive** and **abstractive** summarization using **prompt engineering**.

### 📆 Calendar & Task Manager
- Schedule tasks with a visual calendar interface.
- Automatically sends reminders.
- Can prioritize tasks based on activity patterns.

---

## 🔧 Tech Stack

| Layer        | Technology                                 |
|--------------|---------------------------------------------|
| Backend      | [FastAPI](https://fastapi.tiangolo.com/)    |
| Frontend     | Tailwind CSS v4                            |
| Database     | PostgreSQL                                 |
| AI Features  | Prompt Engineering, RAG, Fine-Tuning (LoRA) |
| Auth         | OAuth2 + JWT                               |
| Deployment   | Dockerized Microservices                   |

---

## 🎓 Target Users

- 🧑‍🎓 **Students** — Primary users managing their own study material and tasks.
- 👩‍🏫 **Instructors (optional)** — Validate student roadmaps and provide feedback.

---

## 📈 Why StudyMateAI?

- ✅ **Role-Aware**: Students and instructors get tailored dashboards.
- ✅ **Modular AI**: Each capability is a standalone microservice.
- ✅ **Academic Focus**: Built to solve actual study-related problems, not generic productivity.

---

## 🧪 Example Use Case

> A student uploads lecture slides and asks StudyMateAI to generate a 3-week study roadmap. Later, they paste in a buggy Flask app and get line-by-line code suggestions. Before finals, they drop in a PDF textbook and receive a summarized version highlighting key chapters to revise.

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.11+
- Docker
- PostgreSQL

### Steps

```bash
# Clone the repository
git clone https://github.com/yourusername/studymateai.git
cd studymateai

# Set up virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI server
uvicorn app.main:app --reload
