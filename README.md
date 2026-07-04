# 🏥 LittleHeart AI Care — AI-Assisted Maternal Health Risk Assessment Platform
> AI-assisted maternal health risk assessment platform that combines deterministic clinical rules, machine learning, and Google Gemini to assist with early pregnancy risk assessment, explain results, and notify healthcare providers of high-risk cases.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg)](https://streamlit.io)
[![Supabase](https://img.shields.io/badge/Supabase-Database%20%26%20Auth-3ECF8E.svg)](https://supabase.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🌐 Live Demo

**Streamlit Application**: [https://littleheart.streamlit.app](https://littleheart.streamlit.app)

---

## 🎯 Project Objectives

LittleHeart AI Care was developed to assist in the early identification of maternal health risks by combining deterministic clinical guidelines, machine learning, and AI-generated explanations. The platform aims to support timely decision-making by patients and healthcare providers while maintaining a transparent and auditable assessment pipeline.

---

## 📑 Table of Contents

- [Live Demo](#-live-demo)
- [Project Objectives](#-project-objectives)
- [System Highlights](#-system-highlights)
- [Features](#-features)
- [Architecture Overview](#️-architecture-overview)
- [Complete Data Flow](#-complete-data-flow)
- [Technology Stack](#️-technology-stack)
- [Clinical Features](#-clinical-features)
- [Folder Structure](#-folder-structure)
- [Clinical AI Pipeline](#-clinical-ai-pipeline)
- [Database Architecture](#️-database-architecture)
- [Security](#️-security)
- [Installation & Local Setup](#-installation--local-setup)
- [API Endpoints](#-api-endpoints)
- [Clinical Workflow](#-clinical-workflow)
- [Current Implementation Status](#-current-implementation-status)
- [Future Roadmap](#-future-roadmap)
- [License](#-license)
- [Acknowledgements](#-acknowledgements)
- [Author](#-author)

---

## ⭐ System Highlights

- Deterministic Rule Engine
- Machine Learning Risk Prediction
- Decision Fusion Architecture
- Gemini AI Explanation Layer
- Real-Time Alert System
- Healthcare Provider Dashboard
- Patient Dashboard
- PDF Report Generation
- Clinical Audit Logging
- Row-Level Security

---

## ✨ Features

- **Triple-Layered Risk Assessment**: Evaluates maternal health using clinical rules, ML (XGBoost), and LLMs (Google Gemini).
- **Fail-Safe Clinical Hierarchy**: Deterministic medical rules strictly override probabilistic machine learning predictions to prevent unsafe risk downgrading.
- **Real-Time Clinical Alerts**: Asynchronous WebSocket broadcasting instantly notifies healthcare providers of critical patient assessments.
- **Role-Based Dashboards**: Distinct interfaces tailored for Expectant Mothers, Triage Nurses/Obstetricians, and System Administrators.
- **Conversational Triage Chatbot**: Guided, state-machine-driven patient data collection interface as a user-friendly alternative to standard forms.
- **Automated Clinical Reports**: Generates downloadable PDF reports summarizing vital signs, ML probabilities, and AI-generated explanations.
- **Production-Oriented Security**: Enforces JWT authentication, strict Supabase Row Level Security (RLS), and immutable clinical audit logs.

---

## 🏗️ Architecture Overview

LittleHeart AI Care operates on a decoupled architecture. The backend is a stateless FastAPI service orchestrating the multi-engine AI pipeline and database persistence. The frontend is a Streamlit application providing real-time WebSocket monitoring and interactive data visualization. All data is persisted securely in Supabase PostgreSQL, utilizing database triggers and RLS policies for strict data governance.

---

## 🔄 Complete Data Flow

1. **Patient Input**: Patient submits vitals and symptoms via the Streamlit Form or Chatbot.
2. **Authentication & Ingestion**: Request is secured via JWT and validated against Pydantic schemas in FastAPI.
3. **Deterministic Evaluation**: `RuleEngine` scans for immediate emergency clinical flags (e.g., severe hypertension).
4. **Machine Learning Prediction**: Background thread processes data through the XGBoost `MLEngine` for probabilistic risk scoring.
5. **Decision Fusion**: `DecisionFusion` algorithm synthesizes the outputs, enforcing the rule that critical physical thresholds override AI logic.
6. **Atomic Persistence**: Results are persisted to Supabase via a highly atomic stored procedure.
7. **AI Explanation**: Gemini generates a structured, patient-friendly explanation from the finalized assessment. It never modifies the clinical decision.
8. **Real-Time Alerting**: Database triggers and the WebSocket `AlertService` broadcast the finalized risk payload to online medical staff.

---

## 🛠️ Technology Stack

**Backend**
- FastAPI

**Frontend**
- Streamlit

**Database**
- Supabase PostgreSQL

**Machine Learning**
- XGBoost
- Scikit-learn

**AI**
- Google Gemini 2.0 Flash

**Authentication**
- Supabase Auth

**Language**
- Python

---

## 📋 Clinical Features

The assessment is performed using the following 15 standardized maternal health features.

| Feature | Type |
|----------|------|
| Age | Integer |
| Trimester | Integer |
| Trimester Weeks | Integer |
| Blood Pressure | Category (0–2) |
| Hemoglobin | Float |
| Swelling | Boolean |
| Headache Severity | Integer (0–3) |
| Vaginal Bleeding | Boolean |
| Diabetes History | Boolean |
| Previous Pregnancy Complications | Boolean |
| Fever | Boolean |
| Blurred Vision | Boolean |
| Heart Rate | Integer |
| Reduced Fetal Movement | Boolean |
| Severe Abdominal Pain | Boolean |

---

## 📁 Folder Structure

<details>
<summary>Click to expand full directory tree</summary>

```text
LittleHeart-Ai/
├── backend/                       # FastAPI Backend
│   ├── api/                       # REST & WebSocket route definitions
│   ├── core/                      # Decision fusion logic
│   ├── engines/                   # Rule, ML, and Gemini assessment engines
│   ├── middleware/                # Tracing, error handling, and JSON logging
│   ├── model/                     # Serialized XGBoost models (.pkl)
│   ├── schemas/                   # Pydantic validation models
│   ├── services/                  # Database, Alerts, Chat, and Metrics services
│   ├── utils/                     # JWT Auth & clinical constants
│   ├── database_schema.sql        # Supabase DDL, RPCs, and RLS policies
│   └── main.py                    # Application entry point
├── frontend_streamlit/            # Streamlit Frontend
│   ├── assets/                    # CSS styles and imagery
│   ├── pages/                     # Multi-page routing (Patient, Provider, Admin)
│   ├── services/                  # API clients, auth, PDF, and chart rendering
│   └── app.py                     # Main dashboard and login interface
├── docker-compose.yml             # Orchestration for full production stack
├── nginx.conf                     # Nginx WAF Configuration
├── requirements.txt               # Backend dependencies
└── requirements_streamlit.txt     # Frontend dependencies
```
</details>

---

## 🧠 Clinical AI Pipeline

The core intelligence of the application relies on distinct engines operating in a strict hierarchy:

- **Rule Engine**: Evaluates the 15 standardized clinical inputs together with deterministic clinical interaction rules and emergency thresholds.
- **ML Engine**: Preprocesses patient data to match an XGBoost pipeline trained on a synthetically generated maternal health dataset, returning anomaly probabilities across `LOW`, `MEDIUM`, and `HIGH` classifications.
- **Decision Fusion**: The orchestrator. It prevents AI hallucinations by ensuring that if the Rule Engine detects a physical emergency, the ML Engine is forcibly overridden. It calculates a final `clinical_confidence` metric based on engine alignment.
- **Gemini Engine**: Constrained by a strict safety list, it acts purely as a translator. It reads the finalized `engine_results` and generates a compassionate, non-diagnostic explanation for the patient.
- **Alert Service**: Listens to the fusion layer. If `HIGH` or `CRITICAL` risk is assigned, it initiates a WebSocket broadcast to all connected healthcare dashboards.

---

## 🗄️ Database Architecture

The system utilizes a PostgreSQL schema managed through Supabase with Row Level Security (RLS), immutable clinical records, and audit logging to provide strong application-level data protection.

| Table | Purpose | Security Notes |
|---|---|---|
| `user_profiles` | Stores patient and provider demographic data. | Extends Supabase Auth profiles. |
| `patient_inputs` | Records raw clinical vitals and symptoms. | Immutable (No UPDATE/DELETE allowed). |
| `engine_results` | Stores the exact scoring breakdown from all AI engines. | Cascade deletes with patient inputs. |
| `alerts` | Tracks provider notifications and acknowledgement status. | Status transitions enforced by CHECK constraints. |
| `audit_logs` | System-level tracing of API usage and model invocations. | Write-only via atomic RPC functions. |
| `patient_risk_history`| Time-series aggregation of patient health degradation. | Populated automatically via Postgres Triggers. |

---

## 🛡️ Security

Security is deeply integrated at both the application and database layers:

- **JWT Authentication**: All API interactions require a Supabase-issued JSON Web Token. Signatures, expiry dates, and issuers are strictly verified.
- **Role-Based Access Control (RBAC)**: Distinct permissions for `patient`, `doctor`, and `admin` roles ensure data privacy.
- **Supabase RLS**: Designed with privacy-focused access control using Supabase Row Level Security.
- **Immutable Clinical Records**: Database constraints physically prevent the alteration or soft-deletion of `patient_inputs` and `engine_results` once written.
- **Audit Logging**: Every assessment triggers a parallel write to an `audit_logs` table for forensic traceability.

---

## 💻 Installation & Local Setup

For full instructions on configuring your environment variables, installing dependencies, and running both the FastAPI backend and Streamlit frontend locally (with or without Docker), please refer to the comprehensive **[Local Setup Guide](LOCAL_SETUP.md)**.

---

## 🔌 API Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|:---:|
| `POST` | `/analyze` | Submit clinical vitals for triple-engine risk assessment. | ✅ JWT |
| `POST` | `/auth/login` | Authenticate a user and return a JWT session token. | ❌ No |
| `POST` | `/auth/register` | Register a new patient or provider in the system. | ❌ No |
| `GET` | `/health` | Application health check, version, and active WS connections. | ❌ No |
| `GET` | `/metrics` | Exposes internal latency and failure rates for Prometheus. | ❌ No |
| `GET` | `/history` | Fetch the authenticated patient's historical assessments. | ✅ JWT |
| `GET` | `/admin/metrics` | Fetch aggregated platform statistics (Admins only). | ✅ JWT |
| `GET` | `/docs` | Auto-generated OpenAPI documentation. | ❌ No |
| `WS` | `/ws/alerts` | Subscribe to real-time high-risk clinical broadcasts. | ✅ JWT |

---

## 🏥 Clinical Workflow

1. **Authentication**: Patient securely logs in to the platform.
2. **Input Phase**: Patient inputs their current vitals (Heart Rate, Blood Pressure, Hemoglobin, etc.) via the clinical dashboard or the conversational AI chatbot.
3. **Assessment Phase**: The payload hits the `/analyze` endpoint. The Rule Engine scans for deterministic emergencies. Concurrently, the XGBoost ML Engine calculates anomaly likelihood.
4. **Fusion Phase**: The application merges both engine outputs, strictly prioritizing human-designed clinical rules.
5. **Persistence**: The final risk categorization is securely logged in PostgreSQL.
6. **Augmentation**: Google Gemini generates a structured, patient-friendly explanation from the finalized assessment.
7. **Action**: If the fusion logic dictates a `HIGH` or `CRITICAL` risk, the WebSocket manager instantly flashes a red alert on all active Triage Nurse and Obstetrician monitors.

---

## ✅ Current Implementation Status

**Backend**
- ✔ FastAPI
- ✔ JSON Logging & Error Handling

**AI**
- ✔ Rule Engine
- ✔ ML Engine (XGBoost)
- ✔ Gemini Engine
- ✔ Decision Fusion

**Database**
- ✔ Supabase PostgreSQL
- ✔ Row Level Security (RLS)
- ✔ Audit Logs & Immutability

**Frontend**
- ✔ Patient Dashboard
- ✔ Provider Dashboard
- ✔ Admin Dashboard

**Infrastructure**
- ✔ Authenticated WebSockets
- ✔ PDF Report Generation

---

## 🔮 Future Roadmap

- **Voice Interaction**: Integration of real-time Speech-to-Text (STT) for hands-free clinical triage during emergencies.
- **Mobile Application**: Porting the Streamlit dashboard into a responsive React Native application for traveling healthcare providers.
- **Clinical Validation**: Stress testing the ML pipeline against larger, blinded real-world hospital datasets.
- **Offline Synchronization**: Implementing local-first architecture for rural clinics with intermittent internet connectivity.
- **Multilingual Support**: Real-time translation of the Gemini explanations into localized languages.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- **Google Gemini**
- **Supabase**
- **FastAPI**
- **Streamlit**
- **Scikit-learn**
- **XGBoost**

---

## 👨‍💻 Author

### Kashif Ansari

- **GitHub**: [https://github.com/ShadyNights](https://github.com/ShadyNights)
- **LinkedIn**: [https://www.linkedin.com/in/kashifansari18](https://www.linkedin.com/in/kashifansari18)
