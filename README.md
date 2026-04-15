# 🩺 LittleHeart AI Care: Technical Specification & Execution Guide

## I. STRATEGIC OVERSIGHT & PRODUCT VISION

### Mission-Critical Summary
LittleHeart AI Care fundamentally resolves the latency and accuracy gap in maternal health triage by deploying a hospital-grade, multi-layered decision support system. It introduces a paradigm shift away from purely generative AI tools by enforcing a strict "Fail-Safe Clinical Hierarchy" where deterministic medical rules outright override machine learning and language models. This prevents fatal misdiagnoses, ensures regulatory compliance, and accelerates clinical response times when life-threatening conditions (e.g., preeclampsia, sepsis) emerge. 

### User & System Personas
- **Target High-Value User**: On-call Obstetricians, Triage Nurses, and expectant mothers requiring rapid, highly-accurate health assessments with transparent clinical reasoning.
- **Edge Case/Adversary**: Malicious actors engaging in prompt injection to alter clinical outcomes, or hypochondriac patients overloading the system with rapid-fire, low-fidelity assessment requests.

### The "Plain English" Domain Glossary
1. **Deterministic Rules Engine**: Code that follows strict, uncompromising medical thresholds (e.g., "If blood pressure > 160/110, trigger crisis alert") that cannot be changed by AI.
2. **XGBoost Ensemble**: A powerful analytical model fine-tuned entirely on structured patient data (like age, BMI, vitals) to detect hidden trends without using language models.
3. **Generative NLP Sandboxing**: The practice of restricting conversational AI (Gemini) solely to translating medical jargon into patient-friendly text, explicitly forbidding it from making diagnoses.
4. **Row Level Security (RLS)**: A database firewall ensuring that Dr. A can mathematically only access records for patients assigned to Dr. A, preventing data leaks at the database logic level.
5. **Atomic Persistence**: Saving a patient record such that it either completely succeeds or completely fails, leaving no fragmented or corrupted medical data.

## II. SYSTEM ARCHITECTURE & CORE LOGIC ENGINE

### System Data Flow
1. **Frontend (Streamlit)**: Collects vitals, symptoms, and chatbot telemetry.
2. **API Layer (FastAPI)**: Receives payload, validates JSON schemas, and authenticates the JWT session.
3. **Triple-Engine Evaluation**:
   - *Phase A (Rules)*: Payload hits raw Python deterministic hardcodes. If critical, flag triggered immediately.
   - *Phase B (ML)*: Payload routed through XGBoost for risk scoring.
   - *Phase C (NLP)*: Vitals and outputs fed to Gemini 2.0 for human-readable summaries.
4. **Persistence (Supabase)**: Final payload + system judgements committed to immutable Postgres instance. 
5. **Alerting (WebSocket)**: Broadcasts crisis flags to Provider Dashboards instantly.

### Feature & Logic Breakdown
- **Deterministic Triage (Layer 1)**: Business logic utilizes direct `> / <` comparative operators mapped directly to CDC/ACOG maternal guidelines. Logic: If `{systolic} >= 160` OR `{proteinuria} == True`, output `CRITICAL_PREECLAMPSIA` and disable ML overrides.
- **Predictive Risk Scoring (Layer 2)**: Standard-scaled inputs feed an `xgboost.Booster.predict()` operation, returning an anomaly likelihood integer (0-100%).
- **Sandboxed NLP Summarization (Layer 3)**: Pydantic schemas enforce Gemini output parsing. Prompt architecture: `[SYSTEM: YOU ARE A TRANSLATOR. DO NOT DIAGNOSE.] [DATA: {vitals}]`.
- **Live Provider Notification**: Asynchronous FastAPI background tasks push JSON telemetry to a WebSocket connection, updating the provider UI state within <200ms.

### Requirement Enforcement
- **FastAPI**: Unmatched for its native asynchronous capabilities and automatic OpenAPI schema generation, making complex, multi-agent AI logic fast and documentable.
- **Supabase/Postgres**: Native RLS is required for HIPAA compliance. Sub-millisecond realtime capabilities are superior to polling.
- **XGBoost**: Outperforms neural networks on standard tabular medical data (vitals, blood panels) and provides high explainability for clinical audits.

### Risk & Mitigation Matrix
| Critical Risk | Failure State | Architectural Mitigation |
| :--- | :--- | :--- |
| **LLM Diagnostic Hallucination** | Gemini wrongly tells a critical patient they are fine. | **Enforced Hierarchy**. Gemini's output is *appended* to the deterministic assessment, never replacing it. The UI hard-codes the red flags over the NLP text. |
| **Data Bleed/PII Leakage** | Patient B sees Patient A's records. | **Supabase RLS Rules**. Database inherently blocks cross-tenant reads; FastAPI backend has no administrative override for standard requests. |
| **WebSocket Race Conditions** | Doctor receives delayed crisis alert. | **Idempotent Webhooks & Polling Fallback**. Clients utilize auto-reconnecting WS hooks, backed up by a 15-second SWR (Stale-While-Revalidate) poll. |

### Data Integrity & Security
- **Input Validation**: Pydantic strictly enforces typing (e.g., Heart rate MUST be integer between 30 and 250). Invalid payloads reject with `422 Unprocessable Entity`.
- **Transactions**: All CRUD operations use Postgres ACID transactions. 
- **Encryption**: AES-256 for data at rest; TLS 1.3 for data in transit. 

## III. FRONTEND ENGINEERING & UX FIDELITY

### Interface Constraints
- **Design System**: Glassmorphic layout emphasizing clinical sterility (whites, medical blues) with stark visual contrasting (deep reds) for danger states.
- **Response Budget**: Form submission to initial diagnostic rendering must occur under 800ms. NLP streaming must begin under 1200ms.
- **Accessibility**: WCAG 2.1 AA compliant contrasting.

### Application State Machine
1. **Boot/Idle**: Connect WebSocket, verify auth token.
2. **Form Entry**: Client-side validation blocks erroneous data (e.g., patient age = 400).
3. **Processing**: UI displays non-blocking loading skeletons.
4. **Evaluation**: Streamlit renders deterministic flags IMMEDIATELY. ML and NLP results populate asynchronously.
5. **Action/Success**: PDF generated, provider alerted, clear "Next Steps" rendered to patient.

## IV. DEVOPS, ARCHITECTURE & DEPLOYMENT PROTOCOL

### The Audit File (AUDIT_LOG_SPEC.md)
- **DECISION 001**: Use Supabase over Custom Postgres. *Reason*: Zero-maintenance auth, realtime out-of-the-box, and immediate RLS implementation.
- **DECISION 002**: Streamlit limitation circumvention. *Reason*: Built custom HTML/CSS injections within Streamlit components to allow live DOM manipulation without constant app reruns. 
- **DECISION 003**: Hardcode Clinical Rules Python side, not DB side. *Reason*: Easier version control and unit testing of maternal clinical guidelines vs testing raw SQL functions.

### Local Environment Setup
Ensure Docker Desktop is running. Setup your `.env` in the root (`d:\LittleHeart Ai Care - Copy (3)\.env`):

```env
SUPABASE_URL=YOUR_URL
SUPABASE_KEY=YOUR_KEY
SUPABASE_JWT_SECRET=YOUR_SECRET
GEMINI_API_KEY=YOUR_KEY
ENV=development
```

Run via Docker-Compose:
```bash
docker-compose up --build -d
```

### Production Deployment
**Target Architecture: AWS ECS (Fargate) + Application Load Balancer**
1. ECR holds the immutable Docker image.
2. Application Load Balancer (ALB) distributes traffic to ECS tasks.
3. HTTPS terminates at the ALB; ALB talks to FastAPI via standard port 80/8000.
4. Scale policy metrics tied to CPU utilization > 60% for aggressive horizontal scaling during hospital shifts.

### Git & Security Hygiene
`.gitignore` file contents:
```text
# Environments
.env
.venv/
env/
venv/
ENV/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so

# Supabase Local
/supabase/.temp/

# OS Files
.DS_Store
Thumbs.db
```

### The Final Push
```bash
# Initialize and link
git init
git add .gitignore
git commit -m "chore: initial security definitions"

# Add remaining architecture
git add .
git commit -m "feat: complete initial LittleHeart AI Care specification and scaffolding"

# Push to secure remote
git branch -M main
git remote add origin git@github.com:YOUR_ORG/littleheart-ai-care.git
git push -u origin main
```
