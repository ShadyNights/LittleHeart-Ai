# 💻 Local Setup & Developer Guide

Follow this guide to get the LittleHeart AI Care system (FastAPI backend + Streamlit frontend) running on your local machine for development, testing, and contributions.

## 📋 1. Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.9+**
- **Git**
- A **Supabase** account (The free tier is completely sufficient)
- A **Google Gemini API Key** (Obtain one from [Google AI Studio](https://aistudio.google.com/))
- *(Optional)* **Docker Desktop** if you intend to run the WAF and full containerized stack.

---

## ☁️ 2. Supabase & Database Setup

The application relies on Supabase for Authentication, PostgreSQL, and Row Level Security (RLS).

1. Create a new project in [Supabase](https://supabase.com).
2. Navigate to **Project Settings -> API** and copy your:
   - `Project URL`
   - `anon` `public` API Key
   - `JWT Secret`
3. Go to the **SQL Editor** in your Supabase dashboard.
4. Copy the entire contents of `backend/database_schema.sql` from this repository.
5. Paste it into the SQL Editor and click **Run**. This will generate all required tables, RPCs, policies, and indexes.

---

## ⚙️ 3. Environment Configuration

1. In the root of the project, copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Open the `.env` file and populate it with your actual keys:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your_actual_anon_key_here
SUPABASE_JWT_SECRET=your_actual_jwt_secret_here

ADMIN_EMAIL=admin@hospital.com
ENV=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:8501
ENABLE_ML=true
ENABLE_GEMINI=true
ENABLE_PERSISTENCE=true
```

> [!WARNING]
> Never commit your real `.env` file to version control. It is already included in `.gitignore`.

---

## 🐍 4. Running Locally (Without Docker)

It is highly recommended to use a Python Virtual Environment to avoid dependency conflicts.

### Step 4A: Install Dependencies

Open a terminal in the root directory of the project:

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# 2. Install backend dependencies
pip install -r requirements.txt

# 3. Install frontend dependencies
pip install -r frontend_streamlit/requirements_streamlit.txt
```

### Step 4B: Start the FastAPI Backend

Keep your virtual environment active and run:

```bash
# Run from the root directory so python can resolve the 'backend' module
uvicorn backend.main:app --reload --port 8000
```
- **API URL**: `http://localhost:8000`
- **Swagger UI Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Step 4C: Start the Streamlit Frontend

Open a **new** terminal window, activate your virtual environment again, and run:

```bash
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Start the Streamlit application
streamlit run frontend_streamlit/app.py
```
- The UI will automatically launch in your browser at: `http://localhost:8501`

---

## 🐳 5. Running with Docker (Production Stack)

If you want to run the full stack identically to a production environment (including the Nginx WAF and Rate Limiting):

1. Ensure Docker Desktop is running.
2. Ensure your `.env` file is fully configured (the docker containers will read directly from it).
3. Open a terminal in the root directory and execute:

```bash
docker-compose up --build
```

This will spin up:
- **Nginx WAF** on Port `80`
- **FastAPI Backend** on Port `8000`
- **Streamlit Frontend** on Port `8501`

You can then access the application via `http://localhost:8501`.

---

## 🧪 6. Verification

Once both services are running, verify the setup:
1. Open the Streamlit App (`http://localhost:8501`).
2. Register a new user account (this will sync directly with your Supabase Auth).
3. Log in and navigate to the **Healthcare Dashboard**.
4. To test the backend diagnostics directly, run the built-in verify script:
   ```bash
   python backend/verify.py
   ```
