# URL to test the system: NOTE: PLEASE DO LET ME KNOW BEFORE TESTING. I WILL TURN the Server ON because the models are runing on my personal GPU. Thank You.   
https://78b3c3d3-5500.inc1.devtunnels.ms/front_end/index.html 


# REMOTE REPO LINK:
https://github.com/haadi777/mgc_developer_ai
# Aurora Heights AI Assistant + Lead Scoring System

This project is a full-stack AI sales assistant and lead prediction application built for Aurora Heights real-estate inquiries.

## 1) Technologies Used

### Backend
- Python 3
- FastAPI for REST API development
- Pydantic for request/response validation
- Pandas for data handling and lead scoring input shaping
- Joblib for loading the trained lead-scoring model
- LangChain + LangGraph for the agentic chat workflow
- Ollama with `llama3.1:8b` model for LLM-based conversation
- SQLite-compatible SQL scripts for the separate data-analysis task

### Frontend
- HTML
- CSS
- Vanilla JavaScript

### Data / ML
- Jupyter Notebook for EDA and model training
- `lead_scoring_model.joblib` as the saved ML pipeline
- `leads.csv` as the source dataset for lead analysis and training

### Project Files
- [main.py](main.py) — API server and business logic
- [tools.py](tools.py) — knowledge base + pricing tools for the AI agent
- [front_end/index.html](front_end/index.html) — main web UI
- [front_end/script.js](front_end/script.js) — frontend behavior and API calls
- [front_end/style.css](front_end/style.css) — styling for chat and lead prediction UI
- [notebook/eda+training.ipynb](notebook/eda%2Btraining.ipynb) — exploratory analysis and model training notebook
- [part_2_sql/schema.sql](part_2_sql/schema.sql) — SQL schema for lead data
- [part_2_sql/queries.sql](part_2_sql/queries.sql) — SQL analytics queries

---

## 2) System Architecture

The project follows a simple three-layer architecture:

1. Frontend Layer
   - A browser-based UI displays the chat assistant and the lead prediction form.
   - It sends user messages to the backend and renders the AI responses.

2. Backend API Layer
   - [main.py](main.py) defines FastAPI endpoints:
     - `POST /chat` for conversational AI responses
     - `POST /predict_lead` for lead conversion probability scoring
   - The backend handles request validation, interacts with the model pipeline, and runs the agentic workflow.

3. AI / ML Layer
   - [tools.py](tools.py) contains the Aurora Heights knowledge base and pricing logic used by the LLM agent.
   - The LLM is connected to LangGraph and can invoke tool functions for:
     - project knowledge lookup
     - price calculations for apartment units
   - A memory-based graph keeps conversation state per `thread_id`.

---

## 3) How the System Works

### A. Chat Assistant Flow

1. The user enters a question in the web UI.
2. The frontend sends a request to the `/chat` endpoint with:
   - `thread_id`
   - `message`
3. The FastAPI backend starts a LangGraph workflow.
4. The LLM agent receives the conversation and system instructions.
5. If the model needs project facts or pricing logic, it calls tool functions from [tools.py](tools.py):
   - `lookup_aurora_heights_knowledge`
   - `calculate_aurora_heights_price`
6. The tool result is returned to the LLM, which generates the final answer.
7. The backend returns the assistant response to the frontend and stores the thread-based conversation state.

### B. Lead Prediction Flow

1. The user selects a city and lead source in the frontend.
2. The frontend sends the request to `/predict_lead`.
3. The backend loads the trained model from `notebook/lead_scoring_model.joblib`.
4. A single-row DataFrame is created from the selected `source_clean` and `city_clean` values.
5. The model predicts the conversion probability.
6. The backend converts probability to:
   - `conversion_probability`
   - `conversion_percentage`
   - `priority_level` (`High`, `Medium`, or `Low`)
7. The response is displayed in the UI.

### C. Knowledge and Pricing Layer

- The AI assistant is not just a generic chatbot; it uses project-specific knowledge stored in [tools.py](tools.py).
- It can answer real-estate and Aurora Heights pricing questions based on structured knowledge and calculation rules.
- The pricing logic includes:
  - base apartment pricing
  - block-specific costs
  - floor premium adjustments
  - corner and Margalla-facing adjustments
  - payment discount rules
  - other charges like utility and parking

---

## 4) Architecture Diagram (Text Summary)

```text
Browser UI (HTML/CSS/JS)
        |
        v
FastAPI Backend (main.py)
        |
        +--> /chat  --> LangGraph Agent --> Ollama LLM --> Tool Calls --> tools.py
        |
        +--> /predict_lead --> joblib model --> lead score result
        |
        +--> MemorySaver per thread_id
```

---

## 5) Independent Task: part_2_sql

This project contains a separate SQL task in the folder [part_2_sql](part_2_sql).

It is independent from the Python backend and frontend application and should be treated as a separate assignment.

Contents:
- [part_2_sql/schema.sql](part_2_sql/schema.sql) — defines the `leads` table and indexes
- [part_2_sql/queries.sql](part_2_sql/queries.sql) — includes SQL queries for:
  - conversion rate by lead source
  - duplicate detection and canonical retention
  - city normalization and conversion analysis

This SQL task is not part of the web application runtime; it is a standalone database/analytics task.

---

## 6) How to Run

### Prerequisites
- Python 3.10+
- pip
- Ollama installed and running locally
- The model `llama3.1:8b` pulled in Ollama

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Ollama
Make sure the local Ollama service is running:
```bash
ollama serve
```

Then pull the required model if it is not already available:
```bash
ollama pull llama3.1:8b
```

### 3. Run the backend
From the project root:
```bash
uvicorn main:app --reload
```

The app will start on:
```text
http://127.0.0.1:8000
```

### 4. Open the frontend
Open the HTML file in the browser or serve the folder with a static server:
```bash
python -m http.server 8001
```
Then open:
```text
http://127.0.0.1:8001/front_end/
```

### 5. Test the API
You can use the provided `test.rest` file or call the endpoints directly:
- `POST /chat`
- `POST /predict_lead`

---

## 7) Summary

This system combines:
- an AI-powered real-estate assistant,
- a lead conversion prediction model,
- a browser-based interface,
- and a separate SQL analysis task.

The main application flow is centered around FastAPI + LangGraph + Ollama, while the ML and SQL components support sales intelligence and lead analytics.
