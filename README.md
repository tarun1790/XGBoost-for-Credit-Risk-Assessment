# Luffy Risk Management: Enterprise Credit Risk Assessment Platform

Luffy Risk Management is a production-ready, explainable AI (XAI) credit risk assessment platform. It uses **FastAPI**, **React.js (with Tailwind CSS)**, **PostgreSQL**, and **XGBoost** to automate credit scorecard modeling and evaluate borrower default risk. 

The platform implements industry-standard credit scorecard scaling (mapping default probabilities to 300–850 credit scores) and features integrated **SHAP explainability** to deliver transparent, auditable credit decisions.

---

## 🛠️ Repository Directory Structure

```text
├── .github/
│   └── workflows/
│       └── ci-cd.yml                 # GitHub Actions CI/CD Pipeline
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth.py           # JWT Registration, Login & Admin Auditing
│   │   │       ├── customers.py      # Borrower profile CRUD (Analyst/Admin)
│   │   │       ├── dashboard.py      # Aggregate portfolio risk summary stats
│   │   │       └── predictions.py    # Risk evaluations (PD, SHAP, Credit Scores)
│   │   ├── core/
│   │   │   ├── config.py             # Pydantic environment configurations
│   │   │   ├── db.py                 # Async SQLAlchemy PostgreSQL connection
│   │   │   └── security.py           # Bcrypt password hashing & JWT generation
│   │   ├── models/
│   │   │   └── models.py             # Database schemas (User, Customer, Prediction, Logs)
│   │   ├── services/
│   │   │   └── ml_service.py         # Singleton ML Inference & SHAP Service
│   │   └── main.py                   # FastAPI entrypoint, Lifecyle, Seeds
│   ├── ml_pipeline/
│   │   ├── data/                     # Data directory (synthetic source CSVs)
│   │   ├── models/                   # Model registry (model.json, preprocessor.pkl, etc.)
│   │   ├── generate_synthetic_data.py# High-fidelity Home Credit dataset generator
│   │   └── train.py                  # XGBoost training, CV evaluation & SHAP serialization
│   ├── tests/
│   │   └── test_api.py               # Async integration & ML unit tests
│   ├── Dockerfile                    # Multi-stage Backend image builder
│   └── requirements.txt              # Backend dependencies list
├── frontend/
│   ├── src/
│   │   ├── context/
│   │   │   └── AuthContext.jsx       # Auth State & Role-Based Access Control (RBAC)
│   │   ├── pages/
│   │   │   ├── Login.jsx             # Glassmorphic Login view
│   │   │   ├── DashboardOverview.jsx # Analytical Charts (Recharts) & recent reports
│   │   │   ├── CustomerDirectory.jsx # Borrower directory & register forms
│   │   │   ├── RiskAssessmentDetails.jsx # SVG score progress gauge & diverging SHAP chart
│   │   │   └── AdminPanel.jsx        # Admin credential provisioning & audit logs search
│   │   ├── services/
│   │   │   └── api.js                # Axios client with JWT request interceptors
│   │   ├── App.jsx                   # React Router configurations & Navigation Layout
│   │   ├── index.css                 # Base Tailwind styles & Glassmorphic utilities
│   │   └── main.jsx                  # React DOM mount script
│   ├── Dockerfile                    # Multi-stage production Nginx frontend builder
│   ├── nginx.conf                    # Nginx proxy-pass and SPA route fallback config
│   ├── package.json                  # Frontend dependencies list
│   └── tailwind.config.js            # Tailwind v3 theme customization config
├── docker-compose.yml                # Unified multi-container orchestration
└── README.md                         # Deployment and methodology guide
```

---

## 📈 Credit Scoring & Risk Methodology

### 1. Model Training
The ML model is trained on a replica of the **Home Credit Default Risk** dataset, incorporating demographic details, financial variables, and external credit bureau ratings (`EXT_SOURCE_1`, `EXT_SOURCE_2`, `EXT_SOURCE_3`). 
- **Preprocessing**: Handles missing values with median imputation for numerical data and mode imputation for categorical data. Categorical features are one-hot encoded, and continuous values are scaled using Scikit-Learn pipelines.
- **XGBoost Classifier**: Configured with GPU auto-detection (`tree_method='hist'`). Evaluated using cross-validation to maximize ROC-AUC.

### 2. Log-Odds Scorecard Scaling
The raw Probability of Default ($PD$) from XGBoost is scaled to a standard credit score ($300$ to $850$) using log-odds scaling:
$$Odds = \frac{1 - PD}{PD}$$
$$Score = Offset + Factor \times \ln(Odds)$$

The scaling constants are calibrated using:
- **Reference Score**: $600$ at $50:1$ odds ($Odds = 50$).
- **Points to Double the Odds (PDO)**: $40$ points (score increases by 40 when the odds of non-default double).

Derived Constants:
- $Factor = \frac{PDO}{\ln(2)} = \frac{40}{\ln(2)} \approx 57.7078$
- $Offset = Score_{ref} - Factor \times \ln(Odds_{ref}) = 600 - 57.7078 \times \ln(50) \approx 374.25$

The final credit score calculation is:
$$Score = \text{clip}\left(374.25 + 57.7078 \times \ln\left(\frac{1 - PD}{PD}\right), 300, 850\right)$$

### 3. SHAP Explainability
The platform computes local feature attributions using `shap.TreeExplainer` on the raw log-odds margins of the XGBoost booster.
For a prediction, the SHAP values sum up to the model's log-odds output:
$$\sum \text{SHAP}_i + \text{base\_value} = \text{log-odds}$$

The React dashboard renders these values in a centered, diverging horizontal bar chart, showing which factors pushed the default risk up (red/adverse) or down (green/favorable).

---

## 🔑 Demo Access Credentials

The database is pre-seeded with two accounts on container startup:

*   **Administrator Account** (Full control over user registration, customer deletion, and viewing audit logs):
    *   **Username**: `admin`
    *   **Password**: `AdminPassword123`
*   **Credit Analyst Account** (Create/edit customer profiles and trigger risk evaluations):
    *   **Username**: `analyst`
    *   **Password**: `AnalystPassword123`

---

## 🚀 Quickstart Guide (Local Docker Compose)

The easiest way to run the entire stack is using **Docker Compose**:

### Prerequisites
- Docker & Docker Compose installed.

### Start the Platform
Run the following command at the repository root:
```bash
docker compose up --build
```
This spins up:
1.  **PostgreSQL** (`db`) on port `5432` (with database `credit_risk`).
2.  **FastAPI Backend** (`backend`) on port `8000`. Runs tables migrations and seeds demo data on launch.
3.  **React Frontend & Nginx** (`frontend`) on port `80`.

Open your browser and navigate to: **`http://localhost`** (or `http://localhost:80`) to access the web application.

---

## 💻 Manual Setup & Local Development

To develop or test components individually without Docker:

### 1. Backend Setup
1.  Navigate to `backend` folder:
    ```bash
    cd backend
    ```
2.  Install Python packages:
    ```bash
    pip install -r requirements.txt
    ```
3.  (Optional) Generate training dataset and fit the XGBoost model locally:
    ```bash
    # Generate CSV files in backend/ml_pipeline/data/
    python ml_pipeline/generate_synthetic_data.py
    
    # Train model, save preprocessor & SHAP explainer to backend/ml_pipeline/models/
    python ml_pipeline/train.py
    ```
4.  Configure environment variables or create a `.env` file:
    ```env
    DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/credit_risk
    JWT_SECRET=your_custom_secret_key_here
    ```
5.  Start the FastAPI application:
    ```bash
    python -m uvicorn app.main:app --reload --port 8000
    ```

### 2. Frontend Setup
1.  Navigate to `frontend` folder:
    ```bash
    cd ../frontend
    ```
2.  Install NPM packages:
    ```bash
    npm install
    ```
3.  Start Vite dev server:
    ```bash
    npm run dev
    ```
    Access the frontend at `http://localhost:5173`. API calls are proxied to `http://localhost:8000` via `vite.config.js`.

---

## 🧪 Running Automated Tests

A comprehensive suite of unit tests for ML predictions and integration tests for auth/RBAC is located in `backend/tests/`.

To run tests locally:
```bash
# Install testing requirements
pip install pytest httpx aiosqlite

# Run the test suite
python -m pytest backend/tests/ -v
```
Tests automatically mock the database utilizing a fast, self-contained, in-memory **async SQLite** database (`sqlite+aiosqlite:///:memory:`).
