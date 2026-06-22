import os
import pickle
import numpy as np
import pandas as pd
import xgboost as xgb
from backend.app.core.config import settings

class MLService:
    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.explainer = None
        self.metadata = None
        self.is_loaded = False
        
    def load_artifacts(self):
        """Loads all serialized model assets from the ml_pipeline registry."""
        if self.is_loaded:
            return
            
        print("Initializing MLService: Loading serialized model artifacts...")
        
        # Check if all files exist
        paths = [
            settings.MODEL_PATH, 
            settings.PREPROCESSOR_PATH, 
            settings.EXPLAINER_PATH, 
            settings.METADATA_PATH
        ]
        if not all(os.path.exists(p) for p in paths):
            raise FileNotFoundError(
                "Model artifacts not found. Please run the training pipeline first to compile the model."
            )
            
        # Load preprocessor
        with open(settings.PREPROCESSOR_PATH, 'rb') as f:
            self.preprocessor = pickle.load(f)
            
        # Load XGBoost model
        self.model = xgb.XGBClassifier()
        self.model.load_model(settings.MODEL_PATH)
        
        # Load SHAP explainer
        with open(settings.EXPLAINER_PATH, 'rb') as f:
            self.explainer = pickle.load(f)
            
        # Load metadata
        with open(settings.METADATA_PATH, 'rb') as f:
            self.metadata = pickle.load(f)
            
        self.is_loaded = True
        print("MLService: All artifacts loaded successfully!")
        
    def feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        """Applies feature engineering transformation to raw customer features."""
        df = df.copy()
        
        # Financial ratios
        df['CREDIT_INCOME_PERCENT'] = df['AMT_CREDIT'] / (df['AMT_INCOME_TOTAL'] + 1e-5)
        df['ANNUITY_INCOME_PERCENT'] = df['AMT_ANNUITY'] / (df['AMT_INCOME_TOTAL'] + 1e-5)
        df['CREDIT_TERM'] = df['AMT_ANNUITY'] / (df['AMT_CREDIT'] + 1e-5)
        df['INCOME_PER_PERSON'] = df['AMT_INCOME_TOTAL'] / (df['CNT_FAM_MEMBERS'] + 1e-5)
        
        # Employment ratios
        df['DAYS_EMPLOYED_ANOM'] = (df['DAYS_EMPLOYED'] == 365243).astype(int)
        df['DAYS_EMPLOYED_CLEANED'] = df['DAYS_EMPLOYED'].replace(365243, np.nan)
        df['DAYS_EMPLOYED_PERCENT'] = df['DAYS_EMPLOYED_CLEANED'] / (df['DAYS_BIRTH'] + 1e-5)
        
        # Age
        df['AGE_YEARS'] = -df['DAYS_BIRTH'] / 365.25
        
        # External sources
        ext_sources = ['EXT_SOURCE_1', 'EXT_SOURCE_2', 'EXT_SOURCE_3']
        df['EXT_SOURCES_MEAN'] = df[ext_sources].mean(axis=1)
        df['EXT_SOURCES_NAN_COUNT'] = df[ext_sources].isna().sum(axis=1)
        
        # Safe geometric mean
        non_zero_sources = df[ext_sources].notna().sum(axis=1).replace(0, np.nan)
        df['EXT_SOURCES_GEOM_MEAN'] = df[ext_sources].prod(axis=1) ** (1 / non_zero_sources)
        
        return df

    def predict(self, raw_data: dict) -> dict:
        """
        Executes prediction, scales PD to Credit Score, and computes SHAP explanations.
        """
        if not self.is_loaded:
            self.load_artifacts()
            
        # Convert dictionary to DataFrame
        df = pd.DataFrame([raw_data])
        
        # Remove target/id if they slip into prediction dictionary
        for col in ['TARGET', 'SK_ID_CURR', 'DAYS_EMPLOYED']:
            if col in df.columns:
                df = df.drop(columns=[col])
                
        # Fill in missing columns if any from training list
        all_train_cols = self.metadata['numerical_cols'] + self.metadata['categorical_cols']
        # We need to construct the pre-engineered columns first.
        # But wait, DAYS_EMPLOYED is needed for feature engineering, so we must add it back if we deleted it
        # Actually, let's keep DAYS_EMPLOYED in raw_data, but drop it during feature engineering split.
        
        df_raw = pd.DataFrame([raw_data])
        
        # Run feature engineering
        df_engineered = self.feature_engineering(df_raw)
        
        # Drop columns not used by preprocessor
        cols_to_drop = ['TARGET', 'SK_ID_CURR', 'DAYS_EMPLOYED']
        for col in cols_to_drop:
            if col in df_engineered.columns:
                df_engineered = df_engineered.drop(columns=[col])
                
        # Match order of columns from training metadata
        expected_cols = self.metadata['numerical_cols'] + self.metadata['categorical_cols']
        
        # Handle cases where some categorical columns might be missing in API input
        for col in expected_cols:
            if col not in df_engineered.columns:
                if col in self.metadata['numerical_cols']:
                    df_engineered[col] = np.nan
                else:
                    df_engineered[col] = "None"
                    
        df_engineered = df_engineered[expected_cols]
        
        # Apply preprocessing (imputing, scaling, encoding)
        X_processed = self.preprocessor.transform(df_engineered)
        
        # Run model inference
        # predict_proba returns probability for class 0 and 1
        probs = self.model.predict_proba(X_processed)
        pd_prob = float(probs[0][1])
        
        # Map PD to Credit Score using log-odds scaling
        # Avoid division by zero or log of zero/negative
        pd_capped = np.clip(pd_prob, 0.0001, 0.9999)
        odds = (1.0 - pd_capped) / pd_capped
        
        # Calibration constants (PDO = 40, ref score = 600 at 50:1 odds)
        factor = 40.0 / np.log(2.0)
        offset = 600.0 - factor * np.log(50.0)
        
        credit_score = int(np.clip(offset + factor * np.log(odds), 300, 850))
        
        # Determine risk category
        if credit_score >= 750:
            risk_category = "Low Risk (Excellent)"
        elif credit_score >= 700:
            risk_category = "Medium-Low Risk (Good)"
        elif credit_score >= 600:
            risk_category = "Medium Risk (Fair)"
        else:
            risk_category = "High Risk (Poor)"
            
        # Calculate SHAP values for the processed sample
        # TreeExplainer returns shape (1, num_features) or (1, num_features, 2)
        shap_vals = self.explainer.shap_values(X_processed)
        if isinstance(shap_vals, list):
            # In some versions of shap, list is returned for classes
            shap_vals = shap_vals[1] if len(shap_vals) > 1 else shap_vals[0]
            
        # Extract features
        if len(shap_vals.shape) > 1:
            shap_vals = shap_vals[0]
            
        feature_names = self.metadata['feature_names']
        shap_dict = dict(zip(feature_names, [float(v) for v in shap_vals]))
        
        # Sort and filter features with significant impact to return
        # But we return all of them so the frontend can choose what to show
        
        return {
            "probability_of_default": pd_prob,
            "credit_score": credit_score,
            "risk_category": risk_category,
            "shap_explanations": shap_dict
        }

# Singleton instance
ml_service = MLService()
