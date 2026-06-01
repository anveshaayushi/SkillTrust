Technical Architecture (Deep Dive)

SkillTrust is designed as a modular multi-agent system where each agent performs a specialized function in the candidate evaluation pipeline. The agents are coordinated through a centralized orchestrator, forming a structured execution flow similar to a directed pipeline.

Agent Workflow
Resume → Profile Agent → Evidence Agent → Skill Testing Agent → Scoring → Output
1. Profile Agent (Resume Intelligence Layer)

Purpose: Extract structured candidate data from unstructured resume files.

Implementation Details:
Parses PDF, DOCX, and TXT files
Uses:
PyMuPDF for PDF text extraction
python-docx for DOCX parsing
Extracted text is passed to the Google Gemini API
Processing:
The LLM extracts:
Skills
Project details
GitHub links
Experience signals
Output:
{
  "skills": ["Python", "React", "SQL"],
  "github": "https://github.com/xyz",
  "projects": [...]
}
2. Evidence Agent (Skill Validation Layer)

Purpose: Validate whether claimed skills are supported by real-world evidence.

Implementation Details:
Fetches repositories using GitHub REST API
Maps resume skills to repository content
Processing:
Evaluates:
Programming languages used
Repository activity and commits
Project relevance to claimed skills
Uses keyword matching and heuristic scoring
Output:
{
  "verified_skills": ["Python", "React"],
  "missing_skills": ["Docker"],
  "confidence_scores": {...}
}
3. GitHub AI Detection Agent

Purpose: Detect low-authenticity or AI-generated code patterns.

Implementation Details:
Analyzes repository code snippets
Compares against known templates
Techniques:
TF-IDF vectorization
Cosine similarity scoring
Pattern-based heuristics
Behavior:
High similarity indicates potential template or copied code
Low structural complexity indicates weak authenticity
4. Skill Testing Agent (Core Intelligence Layer)

Purpose: Dynamically evaluate candidate skills through generated tasks.

Implementation Details:
Takes as input:
Missing skills
Low-confidence skills
Uses Azure OpenAI (GPT-4.1)
Processing:
Generates:
Coding questions
Conceptual questions
System design prompts
Adjusts difficulty level dynamically (beginner, intermediate, advanced)
Output:
{
  "Python": {
    "question": "...",
    "difficulty": "intermediate",
    "status": "pending"
  }
}
5. Scoring and Fraud Detection Engine

Purpose: Compute authenticity scores and detect fraudulent signals.

Implementation Details:
Combines:
Resume similarity score
Evidence confidence score
Skill validation signals
Techniques:
TF-IDF vectorization
Cosine similarity
Weighted scoring model
Output:
{
  "authenticity_score": 0.8,
  "fraud_flag": false,
  "reason": "Work appears original"
}
6. Orchestrator (Pipeline Controller)

Purpose: Coordinate all agents and manage execution flow.

Implementation Details:
Executes agents sequentially:
Profile Agent
Evidence Agent
Skill Testing Agent
Scoring Engine
Handles:
Data transfer between agents
Error handling
Final aggregation of results
Design:
Modular and extensible
Follows a structured pipeline similar to directed graph execution
Data Flow Summary
Raw Resume
   ↓
Text Extraction
   ↓
LLM Skill Extraction
   ↓
GitHub Validation
   ↓
Skill Gap Detection
   ↓
AI Question Generation
   ↓
Scoring and Fraud Detection
   ↓
Frontend Dashboard
System Characteristics
Modular design allowing independent agent updates
Transparent evaluation pipeline with explainable outputs
Scalable architecture supporting additional agents
Hybrid approach combining LLM intelligence with deterministic scoring
