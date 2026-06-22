import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select
from backend.app.core.config import settings
from backend.app.core.db import engine, Base, AsyncSessionLocal
from backend.app.core.security import get_password_hash
from backend.app.models.models import User, Customer
from backend.app.services.ml_service import ml_service
from backend.app.api.v1 import auth, customers, predictions, dashboard

async def seed_data():
    """Create database tables if they do not exist and seed initial system accounts & test customers."""
    async with engine.begin() as conn:
        # Create all tables async
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as db:
        # 1. Seed Admin User
        admin_check = await db.execute(select(User).filter(User.username == "admin"))
        if not admin_check.scalars().first():
            admin_user = User(
                username="admin",
                email="admin@creditrisk.com",
                hashed_password=get_password_hash("AdminPassword123"),
                role="ADMIN",
                is_active=True
            )
            db.add(admin_user)
            print("Seeded default Admin account: admin / AdminPassword123")
            
        # 2. Seed Analyst User
        analyst_check = await db.execute(select(User).filter(User.username == "analyst"))
        if not analyst_check.scalars().first():
            analyst_user = User(
                username="analyst",
                email="analyst@creditrisk.com",
                hashed_password=get_password_hash("AnalystPassword123"),
                role="ANALYST",
                is_active=True
            )
            db.add(analyst_user)
            print("Seeded default Analyst account: analyst / AnalystPassword123")
            
        # 3. Seed test customer records if empty
        customer_check = await db.execute(select(Customer))
        if not customer_check.scalars().first():
            test_customers = [
                Customer(
                    sk_id_curr=100001,
                    first_name="Jane",
                    last_name="Doe",
                    email="jane.doe@example.com",
                    phone="+1234567890",
                    amt_income_total=180000.0,
                    amt_credit=450000.0,
                    amt_annuity=22500.0,
                    days_birth=-14500, # ~39 years old
                    days_employed=-3200, # ~8.7 years employed
                    own_car_age=3.0,
                    region_rating_client=2,
                    ext_source_1=0.65,
                    ext_source_2=0.72,
                    ext_source_3=0.58,
                    name_contract_type="Cash loans",
                    code_gender="F",
                    flag_own_car="Y",
                    flag_own_realty="Y",
                    cnt_children=1,
                    name_income_type="Working",
                    name_education_type="Higher education",
                    name_family_status="Married",
                    name_housing_type="House / apartment"
                ),
                Customer(
                    sk_id_curr=100002,
                    first_name="John",
                    last_name="Smith",
                    email="john.smith@example.com",
                    phone="+1987654321",
                    amt_income_total=90000.0,
                    amt_credit=300000.0,
                    amt_annuity=18000.0,
                    days_birth=-9200, # ~25 years old
                    days_employed=-450, # ~1.2 years employed
                    own_car_age=None,
                    region_rating_client=3,
                    ext_source_1=0.25,
                    ext_source_2=0.31,
                    ext_source_3=0.15,
                    name_contract_type="Cash loans",
                    code_gender="M",
                    flag_own_car="N",
                    flag_own_realty="N",
                    cnt_children=0,
                    name_income_type="Working",
                    name_education_type="Secondary / secondary special",
                    name_family_status="Single / not married",
                    name_housing_type="Rented apartment"
                ),
                Customer(
                    sk_id_curr=100003,
                    first_name="Robert",
                    last_name="Johnson",
                    email="robert.j@example.com",
                    phone="+1555666777",
                    amt_income_total=250000.0,
                    amt_credit=800000.0,
                    amt_annuity=45000.0,
                    days_birth=-20000, # ~54 years old
                    days_employed=365243, # Pensioner / Unemployed
                    own_car_age=5.0,
                    region_rating_client=1,
                    ext_source_1=0.85,
                    ext_source_2=0.88,
                    ext_source_3=0.82,
                    name_contract_type="Cash loans",
                    code_gender="M",
                    flag_own_car="Y",
                    flag_own_realty="Y",
                    cnt_children=0,
                    name_income_type="Pensioner",
                    name_education_type="Higher education",
                    name_family_status="Married",
                    name_housing_type="House / apartment"
                )
            ]
            db.add_all(test_customers)
            print("Seeded default test customers in database.")
            
        await db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup behavior: Seed database and pre-load ML model
    await seed_data()
    try:
        ml_service.load_artifacts()
    except Exception as e:
        print(f"Warning: Model registry could not load artifacts at start: {e}")
    yield
    # Shutdown behavior: Clean up connections
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route Mounting
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(customers.router, prefix=f"{settings.API_V1_STR}/customers", tags=["Customers"])
app.include_router(predictions.router, prefix=f"{settings.API_V1_STR}/predict", tags=["Predictions"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["Dashboard"])

@app.get("/")
def read_root():
    return {"message": "Credit Risk Assessment Platform REST API is operational.", "version": "1.0"}
