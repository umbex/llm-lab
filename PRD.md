# LLM Evolution Lab / Agent Evolution Lab

## **Product Requirements Document (PRD)**

## 1. Overview

**Agent Evolution Lab** is a minimal, Dockerized web application designed for educational purposes.  
It demonstrates—progressively—how a stateless LLM evolves into a contextual, agent-like system through the incremental addition of memory and structured context layers.
The application allows users to toggle contextual “layers” via UI flags and observe how responses change accordingly.

---

## 2. Objectives

- Demonstrate how LLMs behave **without context**
- Show how **context accumulation** affects outputs
- Educate on architectural patterns behind **agent systems**
- Provide a **transparent, inspectable interface** for each layer
- Keep implementation **minimal, explicit, and didactic**

---

## 3. Core Concept

The system is structured as a **progressive activation model**:
| Layer | Description | Effect |
|------|-------------|--------|
| 0 | Stateless LLM | No memory, no context |
| 1 | Session Memory | Chat history included |
| 2 | System Prompt | Identity & role injected |
| 3 | Persistent Memory | Cross-session memory |
| 4 | Knowledge Base | External markdown context |
Each layer is activated via a UI toggle (flag).

---

## 4. User Experience

### 4.1 Layout

- **Main Area**: Chat interface (ChatGPT-like)
- **Sidebar**: Feature flags + contextual inputs
- **Theme**: Minimal dark UI
- **Language**: English (strict)

---

### 4.2 Sidebar Behavior

Flags progressively reveal inputs:
| Flag | Reveals |
|------|--------|
| Session Memory | No input (automatic) |
| System Prompt | Multi-line editable text area |
| Persistent Memory | Memory inspector (read-only/edit) |
| Knowledge Base | File upload (Markdown) |

---

### 4.3 Chat Behavior

- Scroll-based conversation
- Real-time streaming response (optional)
- Clear distinction between:
  - User messages
  - Assistant responses

---

### 4.4 System Status Indicator

- Minimal, low-visibility text line (bottom or corner)
- Displays:
  - Active layers
  - Token usage (optional)
  - Model in use
    **Example:**

status: session ✓ | system ✓ | memory ✗ | kb ✓

---

## 5. Functional Requirements

### 5.1 Stateless Mode (Baseline)

- Each request sent independently
- No previous messages included

---

### 5.2 Session Memory

- Store conversation in runtime (in-memory or client-side)
- Send full message history at each request
  **Structure:**

```json
[
  { "role": "user", "content": "..." },
  { "role": "assistant", "content": "..." }
]

⸻

5.3 System Prompt Layer

* Injected as first message:

{ "role": "system", "content": "..." }

* Editable via UI
* Supports multi-line input

⸻

5.4 Persistent Memory Layer

* Stores extracted facts
* Survives session reload

Options:

* Local JSON file
* Lightweight DB (SQLite)

Behavior:

* Inject summarized memory into prompt
* Optional manual editing

⸻

5.5 Knowledge Base Layer

* Upload .md file
* Parsed and appended to context

Modes:

* Full inclusion
* Chunked (future enhancement)

⸻

6. Prompt Construction Logic

Final prompt structure:

[System Prompt]
[Persistent Memory Summary]
[Knowledge Base Content]
[Conversation History]
[Current User Input]

Each block is conditionally included based on active flags.

⸻

7. Token Management Strategy

Problem: Context grows indefinitely.

Solutions:

* Sliding window (last N messages)
* Periodic summarization
* Memory extraction (facts vs noise)

⸻

8. Technical Architecture

8.1 Stack

* Backend: Python (FastAPI)
* Frontend: Minimal JS (or React optional)
* LLM API: OpenAI
* Containerization: Docker / Docker Compose

⸻

8.2 Environment Configuration

.env

OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL=gpt-5.4-mini

⸻

8.3 Docker Setup

version: "3.9"
services:
  app:
    build: .
    ports:
      - "3000:3000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data

⸻

8.4 File Storage

Type	Path
Uploaded markdown	/data/uploads
Persistent memory	/data/memory.json

⸻

9. API Design

POST /chat

Request:

{
  "message": "User input",
  "flags": {
    "session": true,
    "system": true,
    "memory": false,
    "kb": true
  }
}

Response:

{
  "reply": "Assistant response",
  "status": "session ✓ | system ✓ | memory ✗ | kb ✓"
}

⸻

10. Non-Functional Requirements

* No authentication (local use)
* Fast startup via Docker
* Transparent logic (no hidden abstractions)
* Minimal dependencies

⸻

11. Design Principles

* Explicit over abstract
* Visible over implicit
* Progressive disclosure
* Didactic clarity

⸻

12. Future Enhancements

* Token usage visualization
* Prompt inspector (debug view)
* Layer diff (compare outputs across configs)
* RAG with embeddings
* Tool usage simulation (true agent step)

⸻

13. Reference

Before starting development, review:

GPT Cleaner (existing repository)
/home/admin/projects/gpt-cleaner
→ Evaluate if this could be an inspiration to start from instead of starting from scratch, but we are not using vercel here, it will run locally in the VM as container.

⸻

14. Definition of Done

* All layers independently toggleable
* Prompt composition clearly inspectable
* Chat behavior changes demonstrably per layer
* Fully runnable via Docker
* UI minimal but clear

⸻

15. Summary

Agent Evolution Lab is not a product.
It is a controlled experiment interface.

Its value lies in making visible what is normally hidden:

An LLM is only as “intelligent” as the context you construct around it.

```
