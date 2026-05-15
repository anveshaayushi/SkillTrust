# Person 4 — Skill Testing Agent
# Step-by-step setup guide

## YOUR FILES
```
skill_testing_agent/
├── skill_testing_agent.py   ← Core agent (your main work)
├── api.py                   ← FastAPI wrapper (for integration with Person 1)
├── test_agent.py            ← Tests to verify everything works
└── requirements.txt         ← Python dependencies
```

---

## STEP 1 — Install Python
Make sure you have Python 3.10+.
Check: open terminal and run:
```
python --version
```
If not installed: https://www.python.org/downloads/

---

## STEP 2 — Create a project folder
```
mkdir skilltrust-agent4
cd skilltrust-agent4
```
Copy all 4 files into this folder.

---

## STEP 3 — Create a virtual environment
```
python -m venv venv
```
Activate it:
- Mac/Linux:  source venv/bin/activate
- Windows:    venv\Scripts\activate

You'll see (venv) in your terminal. Good.

---

## STEP 4 — Install dependencies
```
pip install -r requirements.txt
```

---

## STEP 5 — Get your Anthropic API key
1. Go to https://console.anthropic.com
2. Sign up / log in
3. Go to API Keys → Create Key
4. Copy the key (starts with sk-ant-...)

Set it in your terminal:
- Mac/Linux:  export ANTHROPIC_API_KEY="sk-ant-your-key-here"
- Windows:    set ANTHROPIC_API_KEY=sk-ant-your-key-here

---

## STEP 6 — Run the tests first
```
python test_agent.py
```
You should see mostly ✓ marks.
If you see ✗ on API tests, check your API key.

---

## STEP 7 — Run the agent interactively
```
python skill_testing_agent.py
```
Choose option 1 (single skill test) or option 2 (full demo).
This is your main development environment for weeks 1–3.

---

## STEP 8 — Run the API server (for Person 1 integration)
```
python api.py
```
Server starts at http://localhost:8001
Open http://localhost:8001/docs to see the interactive API docs.
Test it from your browser without writing any code.

---

## WEEK BY WEEK PLAN

### Week 1–2 (do this alone)
- [ ] Complete Steps 1–7 above
- [ ] Run option 2 (demo mode) and answer the questions yourself
- [ ] Try all 5 skills: React, SQL, Python, ML, FastAPI
- [ ] Try giving good answers and bad answers — verify scores differ
- [ ] Tweak the evaluation prompt in evaluate_answer() if scores feel wrong
- [ ] Add more tasks to TASK_BANK for reliability

### Week 2–3 (still alone)
- [ ] Run api.py and test via http://localhost:8001/docs
- [ ] Test /generate-task endpoint
- [ ] Test /test-skill endpoint with Postman or the browser UI
- [ ] Pre-generate and save 3 demo tasks (React/SQL/ML) for demo day
- [ ] Make sure calibrate_level() logic feels right — adjust thresholds

### Week 3–4 (with Person 1)
- [ ] Share your API URL with Person 1
- [ ] Person 1 calls your /test-skills-batch endpoint from the orchestrator
- [ ] Test the full flow together

### Week 4 (demo prep)
- [ ] Record a screen capture of the terminal demo as backup
- [ ] Make sure you have hardcoded demo answers ready if live typing fails

---

## HOW TO TEST WITHOUT PERSON 1

Just run skill_testing_agent.py — it works completely standalone.
The api.py is only needed when Person 1 wants to integrate.

---

## WHAT TO TELL PERSON 1 (your interface contract)

Your API runs on: http://localhost:8001 (or deployed URL)

They call:
POST /test-skills-batch
With:
{
  "tests": [
    {"skill": "React", "claimed_level": "intermediate", "evidence_score": 0.7, "candidate_answer": "..."},
    {"skill": "SQL",   "claimed_level": "advanced",     "evidence_score": 0.4, "candidate_answer": "..."}
  ]
}

They get back:
{
  "skill_scores": {
    "React": {"score": 0.78, "verdict": "Pass", ...},
    "SQL":   {"score": 0.55, "verdict": "Partial", ...}
  },
  "overall_test_score": 0.665
}

That's the only thing Person 1 needs from you.
