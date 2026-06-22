import os
import pickle
import numpy as np
import pandas as pd
import xgboost as xgb
import shap
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix

def feature_engineering(df):
    """
    Applies production feature engineering matching enterprise credit scoring techniques.
    """
    df = df.copy()
    
    # 1. Financial ratios
    df['CREDIT_INCOME_PERCENT'] = df['AMT_CREDIT'] / (df['AMT_INCOME_TOTAL'] + 1e-5)
    df['ANNUITY_INCOME_PERCENT'] = df['AMT_ANNUITY'] / (df['AMT_INCOME_TOTAL'] + 1e-5)
    df['CREDIT_TERM'] = df['AMT_ANNUITY'] / (df['AMT_CREDIT'] + 1e-5)
    df['INCOME_PER_PERSON'] = df['AMT_INCOME_TOTAL'] / (df['CNT_FAM_MEMBERS'] + 1e-5)
    
    # 2. Employment ratios
    # DAYS_EMPLOYED has a value 365243 for pensioners/unemployed, which we must handle
    df['DAYS_EMPLOYED_ANOM'] = (df['DAYS_EMPLOYED'] == 365243).astype(int)
    # Replace anomalous days with NaN so simple imputer handles it, or leave it as 0
    df['DAYS_EMPLOYED_CLEANED'] = df['DAYS_EMPLOYED'].replace(365243, np.nan)
    
    # Percentage of life spent employed
    # DAYS_BIRTH is negative, DAYS_EMPLOYED is negative.
    df['DAYS_EMPLOYED_PERCENT'] = df['DAYS_EMPLOYED_CLEANED'] / (df['DAYS_BIRTH'] + 1e-5)
    
    # Age in years
    df['AGE_YEARS'] = -df['DAYS_BIRTH'] / 365.25
    
    # 3. External Source interactions
    ext_sources = ['EXT_SOURCE_1', 'EXT_SOURCE_2', 'EXT_SOURCE_3']
    df['EXT_SOURCES_MEAN'] = df[ext_sources].mean(axis=1)
    df['EXT_SOURCES_NAN_COUNT'] = df[ext_sources].isna().sum(axis=1)
    df['EXT_SOURCES_GEOM_MEAN'] = df[ext_sources].prod(axis=1) ** (1 / df[ext_sources].notna().sum(axis=1).replace(0, np.nan))
    
    return df

def build_preprocessing_pipeline(numerical_cols, categorical_cols):
    """
    Creates standard preprocessing steps for numerical and categorical columns.
    """
    numerical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_transformer, numerical_cols),
            ('cat', categorical_transformer, categorical_cols)
        ]
    )
    
    return preprocessor

def main():
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, 'data')
    models_dir = os.path.join(base_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    train_path = os.path.join(data_dir, 'application_train.csv')
    if not os.path.exists(train_path):
        raise FileNotFoundError(f"Training data not found at {train_path}. Please run generate_synthetic_data.py first.")
        
    print("Loading datasets...")
    df = pd.read_csv(train_path)
    
    # Apply feature engineering
    print("Performing feature engineering...")
    df_engineered = feature_engineering(df)
    
    # Define Target and Drop Keys
    y = df_engineered['TARGET']
    X = df_engineered.drop(columns=['TARGET', 'SK_ID_CURR', 'DAYS_EMPLOYED'])
    
    # Define column lists for preprocessing
    all_numerical = X.select_dtypes(include=[np.number]).columns.tolist()
    all_categorical = X.select_dtypes(exclude=[np.number]).columns.tolist()
    
    print(f"Numerical columns ({len(all_numerical)}): {all_numerical}")
    print(f"Categorical columns ({len(all_categorical)}): {all_categorical}")
    
    # Train-test split
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Build and fit preprocessing pipeline
    print("Fitting preprocessing pipeline...")
    preprocessor = build_preprocessing_pipeline(all_numerical, all_categorical)
    
    # Fit on train data
    X_train_processed = preprocessor.fit_transform(X_train)
    X_val_processed = preprocessor.transform(X_val)
    
    # Get column names after transformation for feature tracking & SHAP values
    cat_encoder = preprocessor.named_transformers_['cat'].named_steps['onehot']
    cat_cols_transformed = cat_encoder.get_feature_names_out(all_categorical).tolist()
    feature_names = all_numerical + cat_cols_transformed
    
    print(f"Total features after preprocessing: {len(feature_names)}")
    
    # Determine execution device for XGBoost
    device = 'cpu'
    tree_method = 'hist'
    try:
        # Create a dummy classifier to probe GPU capability
        probe = xgb.XGBClassifier(tree_method='hist', device='cuda')
        probe.fit(np.array([[1, 2]]), np.array([0]))
        device = 'cuda'
        print("GPU detected! Configuring XGBoost with CUDA support...")
    except Exception as e:
        print(f"GPU check failed ({e}). Defaulting XGBoost to CPU...")
        
    # Instantiate and fit XGBoost model
    print("Training XGBoost Classifier...")
    model = xgb.XGBClassifier(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='auc',
        early_stopping_rounds=30,
        device=device,
        tree_method=tree_method
    )
    
    model.fit(
        X_train_processed, y_train,
        eval_set=[(X_val_processed, y_val)],
        verbose=50
    )
    
    # Evaluate model
    print("Evaluating model...")
    y_pred_prob = model.predict_proba(X_val_processed)[:, 1]
    y_pred = model.predict(X_val_processed)
    
    auc = roc_auc_score(y_val, y_pred_prob)
    print(f"\nValidation ROC-AUC Score: {auc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_val, y_pred))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_val, y_pred))
    
    # Initialize SHAP explainer on validation data
    print("Initializing SHAP TreeExplainer...")
    # Use a small background dataset (e.g. 200 samples) to initialize explainer if needed, 
    # but TreeExplainer on XGBoost works directly with the model
    explainer = shap.TreeExplainer(model)
    
    # Save Artifacts
    print(f"Saving preprocessor pipeline and model files to {models_dir}...")
    
    # Save Preprocessor Pipeline
    preprocessor_path = os.path.join(models_dir, 'preprocessor.pkl')
    with open(preprocessor_path, 'wb') as f:
        pickle.dump(preprocessor, f)
        
    # Save XGBoost Model
    model_path = os.path.join(models_dir, 'model.json')
    model.save_model(model_path)
    
    # Save SHAP Explainer
    explainer_path = os.path.join(models_dir, 'explainer.pkl')
    with open(explainer_path, 'wb') as f:
        pickle.dump(explainer, f)
        
    # Save metadata (features list)
    metadata = {
        'numerical_cols': all_numerical,
        'categorical_cols': all_categorical,
        'feature_names': feature_names
    }
    metadata_path = os.path.join(models_dir, 'metadata.pkl')
    with open(metadata_path, 'wb') as f:
        pickle.dump(metadata, f)
        
    print("ML Pipeline training completed and all artifacts serialized successfully!")

if __name__ == '__main__':
    main()
