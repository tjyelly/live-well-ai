# 🧘 Live Well AI

Live Well AI is an **agentic wellness assistant** that helps users achieve their health goals through a combination of fitness planning, nutrition guidance, hydration/supplement advice, and progress summaries.  

The system is built with **LangGraph** for workflow orchestration and integrates multiple LLM-powered agents that collaborate to produce personalized wellness plans.  

---

## ✨ Features

- **Fitness Planner Agent** 🏋️ – Generates safe and effective workout routines.  
- **Nutritionist Agent** 🥗 – Creates structured 7-day nutrition plans, optionally enhanced with tools (e.g., calorie/macro calculators).  
- **Hydration & Supplement Agent** 💧 – Provides hydration schedules and supplement guidance tailored to the user’s activity.  
- **Summarizer Agent** 📝 – Summarizes the conversation and provides actionable takeaways.  
- **Agent Orchestration with LangGraph** – Manages workflow across agents in sequence:  
  `human → fitness planner → nutritionist → hydration → summarizer`  

---

## 📂 Project Structure

```
live-well-ai-main/
│
├── agents/                # Individual agent implementations
│   ├── fitness_planner.py
│   ├── nutritionist.py
│   ├── hydration_supplement.py
│   └── summarizer.py
│
├── nodes.py               # Node wrappers for agents (LangGraph-compatible)
├── state.py               # Shared state definition
├── main.py                # Entry point: builds and runs the LangGraph workflow
│
├── tools/                 # Optional: utility tools (e.g., macro calculator)
│
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

---

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/live-well-ai.git
cd live-well-ai-main
```

### 2. Create a virtual environment
```bash
python -m venv .venv
```

### 3. Activate the environment
- **Windows (PowerShell)**
  ```bash
  .venv\Scripts\Activate.ps1
  ```
- **macOS/Linux**
  ```bash
  source .venv/bin/activate
  ```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

> If you face dependency conflicts (e.g. `langchain-core`), update with:
```bash
pip install --upgrade langchain langchain-core langchain-openai langgraph
```

### 5. Set environment variables
Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_openai_api_key_here
```

---

## ▶️ Running the Project

```bash
python main.py
```

Example interaction:

```
=== LIVE WELL AI ===
Get started with your wellness journey today!

Let us know your goals and we will tackle them together!
Type 'exit' to end.

You: I want to lose 5kg in 1 month.
```

Agents will sequentially generate:
1. Fitness plan  
2. Nutrition plan  
3. Hydration & supplements  
4. Conversation summary  

---

## 🧩 Logical Architecture

```
User → Human Node → Fitness Planner → Nutritionist → Hydration → Summarizer → Output
```

Each agent updates the shared `State` object with new insights.

---

## 🖥️ Physical Architecture (suggested)

- **Interface**: CLI (current), extensible to Streamlit/Web UI.  
- **Workflow**: LangGraph orchestrator in Python.  
- **LLM Provider**: OpenAI GPT (via `langchain_openai`).  
- **Tooling**: Optional macro calculator or external API integrations.  
- **Deployment**: Can run locally in venv, Docker, or cloud service (Heroku, GCP, AWS).  

---

## 🚀 Future Enhancements

- [ ] Add sleep/stress management agents  
- [ ] Connect to wearable APIs (Fitbit, Apple Health)  
- [ ] Store user profiles & progress in a database  
- [ ] Web UI with charts & plan tracking  

---

## 📜 License
MIT License – free to use, modify, and distribute.
