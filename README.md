# 🧠 MemoryOS

### **AI-Powered Organizational Memory**

> **Capture human experience. Connect organizational knowledge. Never lose what your people have learned.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python\&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit\&logoColor=white)](https://streamlit.io/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Database-purple)](https://www.trychroma.com/)
[![Sentence Transformers](https://img.shields.io/badge/Sentence--Transformers-Embeddings-orange)](https://www.sbert.net/)
[![License](https://img.shields.io/badge/Status-Hackathon%20Prototype-green)]()

---

## 🚨 The Problem

Organizations don't just run on documents.

They run on **experience**.

An experienced technician might know:

> "When H-204 starts overheating after several hours, check the hydraulic circulation before replacing anything."

But where is that knowledge stored?

Usually... **inside the person's head.** 🧠

And when that person:

* 🚪 leaves the organization
* 🔄 changes teams
* 🏖️ isn't available
* 👴 retires

that practical knowledge can disappear with them.

### That's the problem MemoryOS tries to solve.

---

# 💡 What is MemoryOS?

**MemoryOS is an AI-powered organizational memory system that captures, connects, retrieves, and reasons over human experience.**

Instead of only storing manuals and documents, MemoryOS stores **what people have actually experienced**.

```text
👨‍🔧 Human Experience
        ↓
📝 Capture Memory
        ↓
🧠 Semantic Embedding
        ↓
🗄️ ChromaDB
        ↓
🔎 Semantic Retrieval
        ↓
┌────────┼───────────┐
↓        ↓           ↓
🔗       ⚠️          🚨
Related  Conflict    Incident
Memory   Detection   Mode
└────────┼───────────┘
         ↓
       🤖 LLM
         ↓
💡 Grounded Decision Support
```

---

# ✨ What Can MemoryOS Do?

## 🔍 1. Ask MemoryOS

Ask questions in normal language.

For example:

> **"Machine H-204 is overheating after several hours of operation. What should I check first?"**

MemoryOS:

1. 🧠 Converts the question into an embedding
2. 🔎 Searches organizational memories by semantic similarity
3. 📚 Retrieves relevant experiences
4. 🤖 Gives the relevant context to the LLM
5. 💬 Generates a grounded answer
6. 📌 Shows the memories used as sources

### Example

```text
💡 Recommended Action

Check hydraulic fluid level, cooling filter condition,
and circulation.

🔎 Why?

Previous experience with H-204 identified restricted
hydraulic flow and clogged cooling filters as common causes.

⚠️ Things to Avoid

Do not immediately restart the machine if temperature
continues rising.

📊 Knowledge Coverage: Strong Evidence
```

The important part:

> **The LLM isn't answering from generic knowledge alone.**

It's answering using the organization's stored experience.

---

# 📝 2. Capture Human Experience

Anyone with useful practical experience can add a memory.

Each memory contains:

| Field             | Purpose             |
| ----------------- | ------------------- |
| 🏷️ Title         | What happened       |
| 👤 Author Role    | Who experienced it  |
| 📂 Category       | Type of knowledge   |
| 📋 Situation      | What was happening  |
| 🧠 Experience     | What they observed  |
| 💡 Recommendation | What they recommend |
| ⚠️ Warnings       | What to avoid       |
| 🔖 Tags           | Related concepts    |

Example:

```text
Situation:
H-204 temperature increased after prolonged operation.

Experience:
Restricted hydraulic circulation was observed.

Recommendation:
Check hydraulic fluid level and cooling filter.

Warning:
Do not repeatedly restart while temperature continues rising.
```

The experience is then converted into an embedding and stored in ChromaDB.

---

# 🔗 3. Related Memories

Knowledge doesn't exist in isolation.

MemoryOS automatically finds memories that are semantically related.

For example:

```text
              🔥 H-204 Overheating
                      │
          ┌───────────┼───────────┐
          ↓           ↓           ↓
     🔧 Preventive  🌡️ Sensor   🚨 Emergency
       Maintenance    Failure     Shutdown
```

You can explore related memories directly from the Memory Library.

No separate graph database is required.

MemoryOS uses the existing embedding space to discover relationships.

---

# 🗺️ 4. Knowledge Map

The **Knowledge Map** provides a visual way to explore organizational knowledge.

Instead of:

```text
Memory A
Memory B
Memory C
Memory D
```

you can explore:

```text
                🧠 Memory
                   │
        ┌──────────┼──────────┐
        ↓          ↓          ↓
      🔧 Related  ⚠️ Similar  📚 Experience
        │
        ↓
      🔗 More Knowledge
```

Users can explore first-level and second-level relationships between memories.

---

# ⚠️ 5. Conflict Detection

What happens when two experienced people remember the same situation differently?

That's actually valuable information.

For example:

```text
👨‍🔧 Experience A

"Reduce machine load immediately."

            VS

👨‍🔧 Experience B

"Inspect the cooling system first."
```

MemoryOS detects this as a **potential knowledge conflict**.

It does **not** decide which person is correct.

Instead:

> ⚠️ **Potential Knowledge Conflict**
> Two stored experiences contain different recommendations.
> **Human verification recommended.**

Each memory keeps its:

* 👤 Author
* 📅 Date
* 📌 Source
* 💡 Recommendation

### Why?

Because organizational disagreement is itself knowledge.

The system should **surface the disagreement, not hide it.**

---

# 🚨 6. Incident Mode

Sometimes you don't want to browse a knowledge base.

You have a problem **right now**.

That's what Incident Mode is for.

Example:

> 🚨 **"H-204 temperature is rapidly increasing."**

MemoryOS produces a structured response:

### 🚨 Incident

What the employee reported.

### ⚡ Immediate Considerations

Relevant checks supported by previous organizational experience.

### 📚 Previous Incidents

Similar situations that have happened before.

### ⚠️ Warnings

Important warnings preserved from previous experiences.

### 👤 Relevant Experts

Roles associated with the relevant memories.

### 📊 Knowledge Coverage

How much organizational evidence exists for this incident.

### 🔗 Sources

The actual memories used.

---

### 🛡️ Important

Incident Mode is **decision support**, not autonomous control.

It does not:

❌ Operate machinery
❌ Invent previous incidents
❌ Invent experts
❌ Automatically declare something safe
❌ Silently resolve conflicting knowledge

---

# 🧠 How It Works

At its core, MemoryOS uses semantic retrieval + grounded generation.

```text
                 USER
                  │
                  ↓
            💬 Question
                  │
                  ↓
          🧠 Embedding Model
                  │
                  ↓
            🔎 ChromaDB
                  │
                  ↓
        📚 Relevant Memories
                  │
        ┌─────────┼──────────┐
        ↓         ↓          ↓
      🔗 Related ⚠️ Conflict 🚨 Incident
        │         │          │
        └─────────┼──────────┘
                  ↓
               🤖 LLM
                  │
                  ↓
          💡 Grounded Answer
                  │
                  ↓
             📌 Sources
```

---

# 🔬 Why Semantic Search?

Keyword search might fail here.

A user could ask:

> **"Why does the press keep getting hot?"**

while the stored memory is titled:

> **"Hydraulic Press H-204 Overheating"**

The wording is different.

But the **meaning is similar**.

Semantic embeddings allow MemoryOS to find that connection.

---

# 📊 Knowledge Coverage

MemoryOS doesn't just answer everything.

It evaluates how strongly the organization's stored knowledge matches the question.

Possible coverage levels:

🟢 **Strong Evidence**
🟡 **Moderate Evidence**
🟠 **Limited Evidence**
🔴 **Insufficient Evidence**

If there isn't enough organizational knowledge, MemoryOS can say so instead of pretending it knows.

---

# 🛠️ Tech Stack

| Technology                   | Purpose                   |
| ---------------------------- | ------------------------- |
| 🐍 **Python**                | Core application          |
| 🎈 **Streamlit**             | Web interface             |
| 🗄️ **ChromaDB**             | Vector database           |
| 🧠 **Sentence Transformers** | Semantic embeddings       |
| 🤖 **OpenRouter**            | LLM inference             |
| 🔐 **python-dotenv**         | Environment configuration |
| 🧪 **Streamlit AppTest**     | UI testing                |

### Lightweight by design

No unnecessary infrastructure.

❌ PostgreSQL
❌ Redis
❌ Neo4j
❌ Docker
❌ Microservices

The complete prototype can run locally.

---

# 📁 Project Structure

```text
MemoryOS/
│
├── 🖥️ app.py
├── 📦 requirements.txt
├── 🔐 .env.example
├── 🚫 .gitignore
├── 📖 README.md
│
├── 🌱 seed/
│   └── demo_memories.py
│
├── 🧠 src/
│   ├── __init__.py
│   ├── answer_service.py
│   ├── config.py
│   ├── conflict_service.py
│   ├── embeddings.py
│   ├── incident_service.py
│   ├── llm.py
│   ├── memory_service.py
│   ├── relationship_service.py
│   └── vector_store.py
│
├── 🧪 test_memory_engine.py
├── 🧪 test_answer_engine.py
├── 🧪 test_new_features.py
└── 🧪 test_app.py
```

---

# 🚀 Getting Started

## 1️⃣ Clone the repository

```bash
git clone https://github.com/rajmurade/Memoyos.git
cd Memoyos
```

## 2️⃣ Create a virtual environment

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

## 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

## 4️⃣ Configure the environment

Create `.env` using `.env.example`.

```env
OPENROUTER_API_KEY=your_api_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openrouter/free
MEMORY_DISTANCE_THRESHOLD=0.75
```

🔐 **Never commit your `.env` file.**

## 5️⃣ Seed demo memories

```bash
python seed/demo_memories.py --reset
```

## 6️⃣ Run MemoryOS 🚀

```bash
streamlit run app.py
```

The application will open in your browser.

---

# 🧪 Testing

MemoryOS includes automated tests for the core engine, new features, and UI.

Run:

```bash
python test_memory_engine.py
python test_answer_engine.py
python test_new_features.py
python test_app.py
```

### Current validation

✅ Memory engine tests
✅ LLM answer generation
✅ 28 feature checks
✅ Conflict detection
✅ Related memory retrieval
✅ Incident Mode
✅ Insufficient-evidence handling
✅ Metadata preservation
✅ Streamlit AppTest
✅ Python compilation checks

---

# 🏭 Demo Knowledge Base

The current demo contains **14 fictional manufacturing memories** covering topics such as:

🔧 Hydraulic press overheating
⚙️ Conveyor vibration
🖥️ CNC calibration drift
💨 Compressor pressure drops
🧪 Coolant contamination
🚨 Emergency shutdown procedures
🔊 Motor bearing failures
🔥 Welding equipment overheating
🌡️ Temperature sensor failures
🔧 Preventive maintenance
⚠️ Conflicting experiences
🔗 Related maintenance experiences

> ⚠️ All demo manufacturing data is fictional and exists only for demonstration purposes.

---

# 🖥️ Application

MemoryOS currently contains five main sections:

```text
🔍 Ask MemoryOS
        ↓
📝 Capture Memory
        ↓
📚 Memory Library
        ↓
🚨 Incident Mode
        ↓
🗺️ Knowledge Map
```

### 🔍 Ask MemoryOS

Ask questions about organizational experience.

### 📝 Capture Memory

Record new practical knowledge.

### 📚 Memory Library

Browse and explore stored experiences.

### 🚨 Incident Mode

Get structured support during an incident.

### 🗺️ Knowledge Map

Explore relationships between memories.

---

# 🎯 Design Principles

### 🧠 Experience > Documentation

Not everything useful can be written into a manual.

### 🔎 Grounded > Generic

Use organizational evidence whenever possible.

### ⚠️ Preserve disagreement

Different experiences should remain visible.

### 👤 Human review matters

Potential conflicts should be reviewed rather than automatically resolved.

### 🚫 Don't invent organizational knowledge

Incidents, experts, warnings, and sources must come from actual stored memories.

### 🪶 Keep the architecture lightweight

A useful prototype doesn't need unnecessary infrastructure.

---

# 🚧 Current Limitations

MemoryOS is currently a **hackathon prototype**.

Some limitations include:

* 📝 Memory capture is currently manual
* 🤖 LLM quality depends on the configured model
* ⚠️ Conflict detection identifies potential conflicts rather than resolving them
* 🧪 Demo data is fictional
* 🔐 Production authentication is not implemented
* 📋 Enterprise audit logging is not implemented
* 🛡️ Production security and governance would require additional work
* 🏭 It is not an autonomous industrial control system

---

# 🔮 Future Scope

Some possible next steps:

### 🤖 AI-Assisted Memory Capture

Paste an incident report, transcript, or rough notes and let AI structure the memory.

### 👥 Expert Routing

Automatically identify people with relevant experience.

### 🕐 Temporal Memory

Track how organizational knowledge changes over time.

### 📄 Multi-Modal Knowledge

Support documents, images, reports, and eventually other media.

### 🔐 Enterprise Security

Add authentication, authorization, audit logs, and data governance.

### 🧩 Memory Versioning

Track how recommendations evolve as new evidence appears.

### 🏢 Organization-Specific Deployment

Deploy isolated memory systems for individual organizations and teams.

---

# ❤️ Why MemoryOS?

Traditional documentation can tell you:

> **"Here is the official procedure."**

MemoryOS tries to preserve something different:

> **"Here is what someone experienced when this actually happened."**

Organizations spend years building experience.

But a lot of that experience lives inside people rather than systems.

When those people leave or aren't available, part of that accumulated knowledge can disappear.

### MemoryOS turns:

```text
👨‍🔧 Human Experience
        ↓
🧠 Organizational Memory
        ↓
🔗 Connected Knowledge
        ↓
🔎 Semantic Retrieval
        ↓
💡 Grounded Decision Support
```

So instead of asking:

> **"Who knows how to solve this?"**

you can ask:

> # **"What does our organization already know?"** 🧠

---

## ⭐ Project Status

**🚀 Hackathon Prototype**

Built with Python, Streamlit, ChromaDB, Sentence Transformers, and LLM-powered grounded retrieval.

---

### 👨‍💻 Built by

**Raj Murade**

[GitHub](https://github.com/rajmurade)
