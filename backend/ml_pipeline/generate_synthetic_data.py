import os
import numpy as np
import pandas as pd

def generate_data(num_samples=10000, seed=42):
    np.random.seed(seed)
    
    # 1. Primary keys
    sk_ids = np.arange(100001, 100001 + num_samples)
    
    # 2. Features
    # Demographics
    contract_types = np.random.choice(['Cash loans', 'Revolving loans'], size=num_samples, p=[0.9, 0.1])
    genders = np.random.choice(['F', 'M', 'XNA'], size=num_samples, p=[0.65, 0.349, 0.001])
    own_car = np.random.choice(['Y', 'N'], size=num_samples, p=[0.34, 0.66])
    own_realty = np.random.choice(['Y', 'N'], size=num_samples, p=[0.69, 0.31])
    children = np.random.choice([0, 1, 2, 3, 4], size=num_samples, p=[0.70, 0.20, 0.08, 0.018, 0.002])
    
    # Income & Credit Details
    income = np.random.lognormal(mean=11.8, sigma=0.5, size=num_samples) # Median around 135k
    income = np.clip(income, 25000, 1000000)
    
    # Credit is correlated with income
    credit_multiplier = np.random.uniform(2.0, 6.0, size=num_samples)
    credit = income * credit_multiplier
    credit = np.clip(credit, 45000, 2000000)
    
    # Annuity is related to credit (e.g. 5-10% of credit)
    annuity_rate = np.random.uniform(0.04, 0.08, size=num_samples)
    annuity = credit * annuity_rate
    
    # Goods price is slightly lower than credit or equal
    goods_price = credit * np.random.uniform(0.85, 1.0, size=num_samples)
    
    # Categorical features
    income_types = np.random.choice(['Working', 'Commercial associate', 'Pensioner', 'State servant', 'Unemployed'], 
                                    size=num_samples, p=[0.53, 0.23, 0.18, 0.059, 0.001])
    
    education_types = np.random.choice(
        ['Secondary / secondary special', 'Higher education', 'Incomplete higher', 'Lower secondary', 'Academic degree'],
        size=num_samples, p=[0.71, 0.25, 0.03, 0.009, 0.001]
    )
    
    family_statuses = np.random.choice(['Married', 'Single / not married', 'Civil marriage', 'Separated', 'Widow'],
                                       size=num_samples, p=[0.64, 0.15, 0.10, 0.07, 0.04])
    
    housing_types = np.random.choice(['House / apartment', 'With parents', 'Rented apartment', 'Municipal apartment', 'Office apartment', 'Co-op apartment'],
                                     size=num_samples, p=[0.88, 0.05, 0.04, 0.02, 0.008, 0.002])
    
    # Family members count
    fam_members = np.zeros(num_samples, dtype=int)
    for i in range(num_samples):
        if family_statuses[i] in ['Married', 'Civil marriage']:
            fam_members[i] = children[i] + 2
        else:
            fam_members[i] = children[i] + 1
            
    # Age & Employment (Age in days is negative, from -20 to -70 years)
    age_years = np.random.uniform(21, 68, size=num_samples)
    days_birth = -1 * (age_years * 365.25).astype(int)
    
    # Employment (also negative. Pensioners have DAYS_EMPLOYED = 365243 in Home Credit dataset)
    days_employed = np.zeros(num_samples, dtype=int)
    for i in range(num_samples):
        if income_types[i] == 'Pensioner':
            days_employed[i] = 365243
        else:
            max_work_years = age_years[i] - 18
            work_years = np.random.uniform(0.1, max_work_years)
            days_employed[i] = -1 * int(work_years * 365.25)
            
    car_age = np.where(own_car == 'Y', np.random.exponential(scale=7, size=num_samples).astype(int), np.nan)
    car_age = np.clip(car_age, 0, 40)
    
    # External Credit Bureau Sources (0 to 1, higher is better)
    ext_1 = np.random.beta(a=3, b=3, size=num_samples) # symmetrical around 0.5
    ext_2 = np.random.beta(a=4, b=3, size=num_samples)
    ext_3 = np.random.beta(a=3, b=4, size=num_samples)
    
    # Introduce missingness (realistic)
    ext_1[np.random.choice([True, False], size=num_samples, p=[0.5, 0.5])] = np.nan
    ext_3[np.random.choice([True, False], size=num_samples, p=[0.2, 0.8])] = np.nan
    
    # 3. Formulate Log-Odds and Target Variable
    # Higher values of z mean higher risk of default
    # Base risk
    z = -1.2
    
    # External scores reduce risk heavily
    z -= 2.8 * np.nan_to_num(ext_2, nan=0.4)
    z -= 2.2 * np.nan_to_num(ext_3, nan=0.35)
    z -= 1.8 * np.nan_to_num(ext_1, nan=0.45)
    
    # Credit-to-Income ratio increases risk
    credit_income_ratio = credit / income
    z += 0.25 * np.clip(credit_income_ratio, 0, 10)
    
    # Annuity-to-Income ratio increases risk
    annuity_income_ratio = annuity / income
    z += 0.8 * np.clip(annuity_income_ratio, 0, 1)
    
    # Younger age (smaller negative value of DAYS_BIRTH / larger value) increases risk
    z += 0.4 * (1.0 - (age_years / 68.0))
    
    # Unemployed has higher risk
    z += np.where(income_types == 'Unemployed', 1.5, 0.0)
    z += np.where(income_types == 'Working', 0.2, 0.0)
    
    # Lower education has higher risk
    edu_risk = np.where(education_types == 'Secondary / secondary special', 0.3,
                        np.where(education_types == 'Lower secondary', 0.6, 0.0))
    z += edu_risk
    
    # Add random noise
    z += np.random.normal(0, 0.8, size=num_samples)
    
    # Probability of Default
    pd_prob = 1 / (1 + np.exp(-z))
    
    # Target label: Bernoulli trial
    target = np.random.binomial(n=1, p=pd_prob)
    
    # Create DataFrame
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
        'DAYS_BIRTH': days_birth,
        'DAYS_EMPLOYED': days_employed,
        'OWN_CAR_AGE': car_age,
        'CNT_FAM_MEMBERS': fam_members,
        'REGION_RATING_CLIENT': np.random.choice([1, 2, 3], size=num_samples, p=[0.1, 0.7, 0.2]),
        'EXT_SOURCE_1': ext_1,
        'EXT_SOURCE_2': ext_2,
        'EXT_SOURCE_3': ext_3
    })
    
    return df

if __name__ == '__main__':
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    print("Generating synthetic Home Credit Default Risk datasets...")
    
    # Generate Train (12000 samples)
    train_df = generate_data(num_samples=12000, seed=42)
    train_path = os.path.join(data_dir, 'application_train.csv')
    train_df.to_csv(train_path, index=False)
    print(f"Saved application_train.csv ({train_df.shape}) to {train_path}")
    
    # Generate Test (3000 samples, without TARGET column)
    test_df = generate_data(num_samples=3000, seed=99)
    test_df = test_df.drop(columns=['TARGET'])
    test_path = os.path.join(data_dir, 'application_test.csv')
    test_df.to_csv(test_path, index=False)
    print(f"Saved application_test.csv ({test_df.shape}) to {test_path}")
    
    print("Synthetic data generation completed successfully!")
