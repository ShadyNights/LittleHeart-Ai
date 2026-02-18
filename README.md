# 🩺 LittleHeart AI Care
### *Enterprise Hybrid Clinical Intelligence for Maternal Health*

**Status**: 🚀 PRODUCTION-READY (10/10 Hardened)  
**Version**: 4.0.0-PROTOTYPE  
**Core Stack**: FastAPI + Streamlit + Supabase + Gemini 2.0 Flash

LittleHeart AI Care is a hospital-grade maternal health assessment platform. It combines deterministic medical rules with predictive machine learning and advanced generative AI (NLP) to provide a 360-degree clinical decision support system.

---

## 🏛️ Comprehensive Architecture

The platform follows a strict **Fail-Safe Clinical Hierarchy**:

### 1. The Triple-Engine Intelligence
| Layer | Engine Type | Authority | Clinical Role |
| :--- | :--- | :--- | :--- |
| **🥇 Layer 1** | **Deterministic Rules** | **ABSOLUTE** | Catches Red Flags (Crisis/Sepsis). *Unalterable by AI.* |
| **🥈 Layer 2** | **ML Ensemble (XGB)** | **MODERATE** | Detects nuanced risk patterns. *Cannot downgrade Layer 1.* |
| **🥉 Layer 3** | **Gemini 2.0 Flash** | **NLP ONLY** | Generates patient-friendly explanations. *Strictly sandboxed.* |

### 2. Live Monitoring & Alerts
- **WebSocket Gateway**: Real-time push notifications for high-risk assessments.
- **Provider Dashboard**: Live-updating banner for medical staff to respond to critical patient flags instantly.

### 3. Patient Interface
- **Chatbot Companion**: Conversational triage that maps user feelings to clinical metrics.
- **Self-Assessment**: Structured forms with real-time feedback and clinical reasoning.
- **Reporting**: Instant PDF Export of clinical summaries for external consultation.

---

## 🔐 Security & Compliance

- **Supabase Auth**: Integrated Sign-up, Sign-in, and Password Reset flows.
- **Atomic Persistence**: Every assessment is saved with a globally unique `input_id` and logged in an immutable audit trail.
- **Data Privacy**: RLS (Row Level Security) ensures doctors only see assigned patients.
- **Clinical Watermark**: All data exports are tagged with system versioning for legal traceability.

---

## 🛠️ Project Structure
```
LittleHeart AI Care/
├── backend/
│   ├── api/             # FastAPI Orchestrators (Analyze, Chat, History)
│   ├── core/            # Clinical Fusion & Feature Engineering
│   ├── engines/         # Rules, ML (XGBoost), Gemini 2.0
│   ├── services/        # Supabase, Alerts (WS), Audit, Metrics
│   └── database_schema.sql # National Standard SQL
├── frontend_streamlit/
│   ├── pages/           # Patient, Provider, and Admin Dashboards
│   ├── services/        # Auth, API Client, PDF Export, Charts
│   └── assets/          # Custom Glassmorphism Styles & ECG Animation
└── tests/               # 🩺 Multi-layer System Verification Suite
```

---

## 🚀 Quick Start Guide

### 1. Environment Requirements
Create a `.env` file in the root directory:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret
GEMINI_API_KEY=your-google-gemini-key
ENV=development
```

### 2. Installation
```bash
# Backend Dependencies
pip install -r requirements.txt

# Frontend Dependencies
pip install -r frontend_streamlit/requirements_streamlit.txt
```

### 3. Execution
```bash
# Start Backend (Port 8000)
uvicorn backend.main:app --reload

# Start Frontend (Port 8501)
streamlit run frontend_streamlit/app.py
```

---

## ⚖️ Clinical Disclaimer
This platform is a clinical decision support system. It is designed for medical professionals to augment care. It is **not** a self-diagnostic device. All assessments must be verified by a licensed healthcare provider in accordance with local healthcare regulations.

---
*© 2026 LittleHeart AI Care | Built for Clinical Excellence*
