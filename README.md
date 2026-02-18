# 🏥 LittleHeart Ai Care: Definitive Maternal Health Platform (10/10)

## 🏁 System Overview
**Status**: 🚀 PRODUCTION-READY (10/10 Hardened)
**Type**: Enterprise Hybrid Clinical Intelligence
**Architecture**: FastAPI + Supabase + Ensemble AI (Rules, ML, LLM)
**LLM Core**: Gemini 2.0 Flash

This platform is a hospital-grade maternal health assessment engine designed for clinical pilots. It goes beyond basic prediction by implementing a deterministic "Fail-Safe" hierarchy with absolute data traceability.

---

## 🏗️ The 10/10 Architecture Ceiling

### 1. Hybrid Decision Hierarchy
| Layer | Engine | Authority | Clinical Role |
| :--- | :--- | :--- | :--- |
| **🥇 Layer 1** | **Deterministic Rules** | **ABSOLUTE** | Catches Red Flags (Hypertensive Crisis, Sepsis). *Unalterable.* |
| **🥈 Layer 2** | **ML Ensemble (XGB)** | **HIGH** | Detects nuanced patterns. Escalates risk levels. *Cannot downgrade Layer 1.* |
| **🥉 Layer 3** | **Gemini 2.0 Flash** | **NLP Only** | Generates empathetic, patient-friendly explanations. *Strictly sandboxed.* |

### 2. Hospital-Grade Database (Supabase)
*   **Legal Traceability**: Automatic capture of `ip_address` and `user_agent` for every clinical entry.
*   **Medical Immutability**: RLS (Row Level Security) prevents any updates or deletions of clinical entries (`patient_inputs`, `engine_results`).
*   **Physiological Integrity**: DB-level consistency checks (e.g., Trimester vs Weeks alignment).
*   **Automated Triggers**: SQL-level automation for longitudinal risk history and high-risk alert generation.

### 3. Privacy & Security
*   **Assigned Visibility**: Doctors strictly only view data for patients assigned to them via `patient_assignments`.
*   **Service Sandboxing**: Database insertions for AI results are restricted to the `service_role` (Backend only).
*   **Soft-Deletion**: Patient records are preserved as `is_active=FALSE` but never deleted, adhering to medical record retention laws.

---

## 🛠️ Project Structure
```
LittleHeart Ai Care/
├── backend/
│   ├── api/             # FastAPI Orchestrators
│   ├── core/            # Clinical Logic & Feature Engineering
│   ├── engines/         # Decision Engines (Rules, ML, Gemini 2.0)
│   ├── services/        # Supabase, Notifications, Audit Logging
│   ├── schemas/         # Unified Clinical Models
│   ├── utils/           # JWT, Auth, Security
│   └── database_schema.sql # National Standard SQL
├── interactive_engines.py # Hardened CLI Harness
└── requirements.txt
```

---

## 🚀 Deployment

### 1. Database Setup
1. Create a new Supabase project.
2. Run the definitive script: `backend/database_schema.sql` in the SQL Editor.

### 2. Environment Configuration
Create a `.env` file:
```env
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_service_role_key
GEMINI_API_KEY=your_gemini_2.0_key
```

### 3. Server Initialization
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

---

## 🛡️ Safety & Compliance (V3.0)
- **Zero-Hallucination**: Output symptoms are validated against input constraints.
- **Medication Block**: Hard-coded rejection of prescription/dosage suggestions.
- **Audit Logs**: 100% trace of every assessment linked to user and metadata.
- **Model Drift Monitoring**: Active `model_drift_logs` table for ML auditability.

---

**Disclaimer**: This platform is a clinical decision support system. It is designed for medical professionals to augment care. It is **not** a diagnostic device and must be used in accordance with local healthcare regulations.
