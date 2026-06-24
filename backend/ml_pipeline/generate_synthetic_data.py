"""
generate_synthetic_data.py

Generates an expanded synthetic Home Credit-style dataset for credit risk modelling.

Enhancements over v1:
  - 50,000 training samples (was 12,000) and 10,000 test samples (was 3,000)
  - 12 additional engineered features covering bureau history, payment behaviour,
    instalment patterns, and social / demographic signals
  - Richer, more realistic correlations and missingness patterns
  - A second validation holdout CSV (3,000 samples) for offline evaluation
  - Reproducible via explicit random seed arguments
"""

import os
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Core generator
# ---------------------------------------------------------------------------

def generate_data(num_samples: int = 50_000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # 1. Primary keys
    # ------------------------------------------------------------------
    sk_ids = np.arange(100_001, 100_001 + num_samples)

    # ------------------------------------------------------------------
    # 2. Demographics
    # ------------------------------------------------------------------
    contract_types = rng.choice(
        ['Cash loans', 'Revolving loans'], size=num_samples, p=[0.90, 0.10]
    )
    genders = rng.choice(['F', 'M', 'XNA'], size=num_samples, p=[0.65, 0.349, 0.001])
    own_car = rng.choice(['Y', 'N'], size=num_samples, p=[0.34, 0.66])
    own_realty = rng.choice(['Y', 'N'], size=num_samples, p=[0.69, 0.31])
    children = rng.choice([0, 1, 2, 3, 4], size=num_samples, p=[0.70, 0.20, 0.08, 0.018, 0.002])

    # ------------------------------------------------------------------
    # 3. Income & credit details
    # ------------------------------------------------------------------
    income = rng.lognormal(mean=11.8, sigma=0.5, size=num_samples)
    income = np.clip(income, 25_000, 1_000_000)

    credit_multiplier = rng.uniform(2.0, 6.0, size=num_samples)
    credit = np.clip(income * credit_multiplier, 45_000, 2_000_000)

    annuity_rate = rng.uniform(0.04, 0.08, size=num_samples)
    annuity = credit * annuity_rate

    goods_price = credit * rng.uniform(0.85, 1.0, size=num_samples)

    # ------------------------------------------------------------------
    # 4. Categorical features
    # ------------------------------------------------------------------
    income_types = rng.choice(
        ['Working', 'Commercial associate', 'Pensioner', 'State servant', 'Unemployed'],
        size=num_samples, p=[0.53, 0.23, 0.18, 0.059, 0.001]
    )
    education_types = rng.choice(
        ['Secondary / secondary special', 'Higher education',
         'Incomplete higher', 'Lower secondary', 'Academic degree'],
        size=num_samples, p=[0.71, 0.25, 0.03, 0.009, 0.001]
    )
    family_statuses = rng.choice(
        ['Married', 'Single / not married', 'Civil marriage', 'Separated', 'Widow'],
        size=num_samples, p=[0.64, 0.15, 0.10, 0.07, 0.04]
    )
    housing_types = rng.choice(
        ['House / apartment', 'With parents', 'Rented apartment',
         'Municipal apartment', 'Office apartment', 'Co-op apartment'],
        size=num_samples, p=[0.88, 0.05, 0.04, 0.02, 0.008, 0.002]
    )
    organization_types = rng.choice(
        ['Business Entity Type 3', 'School', 'Government', 'Self-employed',
         'Medicine', 'Business Entity Type 2', 'Transport: type 3',
         'Industry: type 11', 'Construction', 'Security'],
        size=num_samples
    )

    # ------------------------------------------------------------------
    # 5. Family members count
    # ------------------------------------------------------------------
    fam_members = np.where(
        np.isin(family_statuses, ['Married', 'Civil marriage']),
        children + 2, children + 1
    )

    # ------------------------------------------------------------------
    # 6. Age & employment (in days, negative convention)
    # ------------------------------------------------------------------
    age_years = rng.uniform(21, 68, size=num_samples)
    days_birth = (-1 * age_years * 365.25).astype(int)

    days_employed = np.zeros(num_samples, dtype=int)
    for i in range(num_samples):
        if income_types[i] == 'Pensioner':
            days_employed[i] = 365_243
        else:
            max_work = age_years[i] - 18
            days_employed[i] = int(-1 * rng.uniform(0.1, max_work) * 365.25)

    car_age = np.where(
        own_car == 'Y',
        np.clip(rng.exponential(scale=7, size=num_samples), 0, 40),
        np.nan
    )

    # ------------------------------------------------------------------
    # 7. External credit-bureau scores (0‒1, higher = better)
    # ------------------------------------------------------------------
    ext_1 = rng.beta(a=3, b=3, size=num_samples)
    ext_2 = rng.beta(a=4, b=3, size=num_samples)
    ext_3 = rng.beta(a=3, b=4, size=num_samples)

    # Realistic missingness
    ext_1[rng.random(num_samples) < 0.50] = np.nan
    ext_3[rng.random(num_samples) < 0.20] = np.nan

    # ------------------------------------------------------------------
    # 8. NEW — Bureau history features
    # ------------------------------------------------------------------
    # Number of previous credit applications at bureau
    amt_req_bureau_year = rng.integers(0, 15, size=num_samples).astype(float)
    amt_req_bureau_year[rng.random(num_samples) < 0.05] = np.nan

    # Days since last bureau enquiry
    days_last_phone_change = rng.integers(-2000, 0, size=num_samples).astype(float)

    # Number of active credit lines at bureau
    bureau_active_count = rng.integers(0, 12, size=num_samples).astype(float)
    bureau_active_count[rng.random(num_samples) < 0.10] = np.nan

    # Overdue days on bureau credits (0 means none)
    bureau_overdue_days = np.maximum(
        0, rng.normal(loc=0, scale=15, size=num_samples)
    ).astype(float)
    bureau_overdue_days[rng.random(num_samples) < 0.30] = 0.0  # many have none

    # ------------------------------------------------------------------
    # 9. NEW — Previous application / instalment features
    # ------------------------------------------------------------------
    # Number of previous applications at the same lender
    prev_applications = rng.integers(0, 20, size=num_samples).astype(float)

    # Average instalment payment deviation (positive = overpaid, negative = underpaid)
    instalment_payment_diff = rng.normal(loc=50, scale=500, size=num_samples)

    # Number of missed instalments in past loans
    missed_instalments = np.maximum(
        0, rng.integers(-2, 8, size=num_samples)
    ).astype(float)
    missed_instalments[rng.random(num_samples) < 0.40] = 0.0

    # ------------------------------------------------------------------
    # 10. NEW — Social / flag features
    # ------------------------------------------------------------------
    flag_work_phone = rng.choice([0, 1], size=num_samples, p=[0.78, 0.22])
    flag_email = rng.choice([0, 1], size=num_samples, p=[0.57, 0.43])
    region_rating_client = rng.choice([1, 2, 3], size=num_samples, p=[0.10, 0.70, 0.20])
    region_rating_client_w_city = np.clip(
        region_rating_client + rng.integers(-1, 2, size=num_samples), 1, 3
    )
    # Number of social-circle defaults observed
    obs_30_cnt_social_circle = rng.integers(0, 10, size=num_samples).astype(float)
    obs_30_cnt_social_circle[rng.random(num_samples) < 0.60] = 0.0
    def_30_cnt_social_circle = np.minimum(
        obs_30_cnt_social_circle,
        rng.integers(0, 5, size=num_samples).astype(float)
    )

    # ------------------------------------------------------------------
    # 11. Target — log-odds model
    # ------------------------------------------------------------------
    z = -1.2

    # External bureau scores (dominant signal)
    z -= 2.8 * np.nan_to_num(ext_2, nan=0.40)
    z -= 2.2 * np.nan_to_num(ext_3, nan=0.35)
    z -= 1.8 * np.nan_to_num(ext_1, nan=0.45)

    # Financial stress ratios
    credit_income_ratio = credit / income
    z += 0.25 * np.clip(credit_income_ratio, 0, 10)
    z += 0.80 * np.clip(annuity / income, 0, 1)

    # Age effect (younger = riskier)
    z += 0.40 * (1.0 - age_years / 68.0)

    # Income type
    z += np.where(income_types == 'Unemployed', 1.5, 0.0)
    z += np.where(income_types == 'Working', 0.2, 0.0)

    # Education
    z += np.where(education_types == 'Secondary / secondary special', 0.30, 0.0)
    z += np.where(education_types == 'Lower secondary', 0.60, 0.0)

    # Bureau history signals
    z += 0.05 * np.nan_to_num(amt_req_bureau_year, nan=3.0)
    z += 0.04 * np.nan_to_num(bureau_active_count, nan=3.0)
    z += 0.006 * bureau_overdue_days

    # Instalment behaviour
    z += 0.15 * missed_instalments
    z -= 0.0001 * np.clip(instalment_payment_diff, -1000, 1000)

    # Social circle defaults
    z += 0.10 * def_30_cnt_social_circle

    # Gaussian noise
    z += rng.normal(0, 0.8, size=num_samples)

    pd_prob = 1.0 / (1.0 + np.exp(-z))
    target = rng.binomial(n=1, p=pd_prob)

    # ------------------------------------------------------------------
    # 12. Assemble DataFrame
    # ------------------------------------------------------------------
    df = pd.DataFrame({
        'SK_ID_CURR': sk_ids,
        'TARGET': target,
        'NAME_CONTRACT_TYPE': contract_types,
        'CODE_GENDER': genders,
        'FLAG_OWN_CAR': own_car,
        'FLAG_OWN_REALTY': own_realty,
        'CNT_CHILDREN': children,
        'AMT_INCOME_TOTAL': income,
        'AMT_CREDIT': credit,
        'AMT_ANNUITY': annuity,
        'AMT_GOODS_PRICE': goods_price,
        'NAME_INCOME_TYPE': income_types,
        'NAME_EDUCATION_TYPE': education_types,
        'NAME_FAMILY_STATUS': family_statuses,
        'NAME_HOUSING_TYPE': housing_types,
        'ORGANIZATION_TYPE': organization_types,
        'DAYS_BIRTH': days_birth,
        'DAYS_EMPLOYED': days_employed,
        'OWN_CAR_AGE': car_age,
        'CNT_FAM_MEMBERS': fam_members,
        'REGION_RATING_CLIENT': region_rating_client,
        'REGION_RATING_CLIENT_W_CITY': region_rating_client_w_city,
        'FLAG_WORK_PHONE': flag_work_phone,
        'FLAG_EMAIL': flag_email,
        'EXT_SOURCE_1': ext_1,
        'EXT_SOURCE_2': ext_2,
        'EXT_SOURCE_3': ext_3,
        # New bureau / behaviour features
        'AMT_REQ_CREDIT_BUREAU_YEAR': amt_req_bureau_year,
        'DAYS_LAST_PHONE_CHANGE': days_last_phone_change,
        'BUREAU_ACTIVE_COUNT': bureau_active_count,
        'BUREAU_OVERDUE_DAYS': bureau_overdue_days,
        'PREV_APPLICATIONS_COUNT': prev_applications,
        'INSTALMENT_PAYMENT_DIFF': instalment_payment_diff,
        'MISSED_INSTALMENTS': missed_instalments,
        'OBS_30_CNT_SOCIAL_CIRCLE': obs_30_cnt_social_circle,
        'DEF_30_CNT_SOCIAL_CIRCLE': def_30_cnt_social_circle,
    })

    return df


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)

    print("=" * 60)
    print("Generating expanded synthetic Home Credit datasets…")
    print("=" * 60)

    # Training set — 50,000 samples
    print("\n[1/3] Generating training set (50,000 samples)…")
    train_df = generate_data(num_samples=50_000, seed=42)
    train_path = os.path.join(data_dir, 'application_train.csv')
    train_df.to_csv(train_path, index=False)
    default_rate = train_df['TARGET'].mean()
    print(f"  Saved -> {train_path}  shape={train_df.shape}  default_rate={default_rate:.3%}")

    # Validation set — 3,000 samples (with TARGET, for offline eval)
    print("\n[2/3] Generating validation set (3,000 samples)…")
    val_df = generate_data(num_samples=3_000, seed=777)
    val_path = os.path.join(data_dir, 'application_val.csv')
    val_df.to_csv(val_path, index=False)
    print(f"  Saved -> {val_path}  shape={val_df.shape}")

    # Test set — 10,000 samples (no TARGET)
    print("\n[3/3] Generating test set (10,000 samples)…")
    test_df = generate_data(num_samples=10_000, seed=99)
    test_df = test_df.drop(columns=['TARGET'])
    test_path = os.path.join(data_dir, 'application_test.csv')
    test_df.to_csv(test_path, index=False)
    print(f"  Saved -> {test_path}  shape={test_df.shape}")

    print("\n✅  Data generation completed successfully!")
