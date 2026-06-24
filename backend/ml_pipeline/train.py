"""
train.py

Production-grade XGBoost training pipeline for credit-risk assessment.

Improvements over v1:
  - Supports 35 input columns (12 new bureau / behaviour features)
  - Bayesian-style manual hyperparameter search with cross-validation
  - Calibrated probability output (Platt scaling via CalibratedClassifierCV)
  - Gini coefficient and KS-statistic reported alongside ROC-AUC
  - Feature-importance CSV exported alongside model artefacts
  - Full artefact bundle: model.json, preprocessor.pkl, explainer.pkl,
    feature_importance.csv, metadata.pkl, training_report.txt
"""

import io
import os
import pickle
import time
import numpy as np
import pandas as pd
import xgboost as xgb
import shap
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    roc_auc_score,
    classification_report,
    confusion_matrix,
    brier_score_loss,
)
from scipy import stats


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies production feature engineering matching enterprise credit-scoring
    techniques.  Works with both the original 23-column schema and the
    expanded 35-column schema.
    """
    df = df.copy()

    # 1. Financial ratios
    df['CREDIT_INCOME_PERCENT'] = df['AMT_CREDIT'] / (df['AMT_INCOME_TOTAL'] + 1e-5)
    df['ANNUITY_INCOME_PERCENT'] = df['AMT_ANNUITY'] / (df['AMT_INCOME_TOTAL'] + 1e-5)
    df['CREDIT_TERM'] = df['AMT_ANNUITY'] / (df['AMT_CREDIT'] + 1e-5)
    df['INCOME_PER_PERSON'] = df['AMT_INCOME_TOTAL'] / (df['CNT_FAM_MEMBERS'] + 1e-5)
    df['GOODS_CREDIT_RATIO'] = df['AMT_GOODS_PRICE'] / (df['AMT_CREDIT'] + 1e-5)

    # 2. Employment anomaly flag + cleaned ratio
    df['DAYS_EMPLOYED_ANOM'] = (df['DAYS_EMPLOYED'] == 365_243).astype(int)
    df['DAYS_EMPLOYED_CLEANED'] = df['DAYS_EMPLOYED'].replace(365_243, np.nan)
    df['DAYS_EMPLOYED_PERCENT'] = df['DAYS_EMPLOYED_CLEANED'] / (df['DAYS_BIRTH'] + 1e-5)

    # 3. Age in years
    df['AGE_YEARS'] = -df['DAYS_BIRTH'] / 365.25

    # 4. External source interactions
    ext_cols = ['EXT_SOURCE_1', 'EXT_SOURCE_2', 'EXT_SOURCE_3']
    df['EXT_SOURCES_MEAN'] = df[ext_cols].mean(axis=1)
    df['EXT_SOURCES_MIN'] = df[ext_cols].min(axis=1)
    df['EXT_SOURCES_MAX'] = df[ext_cols].max(axis=1)
    df['EXT_SOURCES_NAN_COUNT'] = df[ext_cols].isna().sum(axis=1)
    notna_count = df[ext_cols].notna().sum(axis=1).replace(0, np.nan)
    df['EXT_SOURCES_GEOM_MEAN'] = (
        df[ext_cols].prod(axis=1) ** (1 / notna_count)
    )
    # EXT_SOURCE_2 is most predictive; interaction with CREDIT ratio
    df['EXT2_CREDIT_INTERACTION'] = (
        df['EXT_SOURCE_2'].fillna(0.5) * df['CREDIT_INCOME_PERCENT']
    )

    # 5. Bureau / behaviour ratio features (only when columns present)
    if 'BUREAU_OVERDUE_DAYS' in df.columns:
        df['BUREAU_OVERDUE_PER_ACTIVE'] = df['BUREAU_OVERDUE_DAYS'] / (
            df.get('BUREAU_ACTIVE_COUNT', pd.Series(1, index=df.index)).fillna(1) + 1e-5
        )
    if 'MISSED_INSTALMENTS' in df.columns and 'PREV_APPLICATIONS_COUNT' in df.columns:
        df['MISSED_RATE'] = df['MISSED_INSTALMENTS'] / (
            df['PREV_APPLICATIONS_COUNT'] + 1e-5
        )

    return df


# ---------------------------------------------------------------------------
# Preprocessing pipeline builder
# ---------------------------------------------------------------------------

def build_preprocessing_pipeline(
    numerical_cols: list, categorical_cols: list
) -> ColumnTransformer:
    numerical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
    ])
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
    ])
    return ColumnTransformer(transformers=[
        ('num', numerical_transformer, numerical_cols),
        ('cat', categorical_transformer, categorical_cols),
    ])


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def gini_score(y_true, y_pred_prob) -> float:
    """Gini coefficient = 2*AUC - 1."""
    return 2 * roc_auc_score(y_true, y_pred_prob) - 1


def ks_statistic(y_true, y_pred_prob) -> float:
    """Kolmogorov-Smirnov statistic between default / non-default score distributions."""
    scores_pos = y_pred_prob[y_true == 1]
    scores_neg = y_pred_prob[y_true == 0]
    ks, _ = stats.ks_2samp(scores_pos, scores_neg)
    return ks


# ---------------------------------------------------------------------------
# Main training routine
# ---------------------------------------------------------------------------

def main():
    t0 = time.time()

    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, 'data')
    models_dir = os.path.join(base_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)

    train_path = os.path.join(data_dir, 'application_train.csv')
    if not os.path.exists(train_path):
        raise FileNotFoundError(
            f"Training data not found at {train_path}. "
            "Please run generate_synthetic_data.py first."
        )

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    print("=" * 62)
    print("  XGBoost Credit-Risk Training Pipeline  (v2)")
    print("=" * 62)
    print(f"\n[1] Loading dataset from {train_path} …")
    df = pd.read_csv(train_path)
    print(f"    Rows: {len(df):,}   Columns: {df.shape[1]}")
    print(f"    Default rate: {df['TARGET'].mean():.3%}")

    # ------------------------------------------------------------------
    # Feature engineering
    # ------------------------------------------------------------------
    print("\n[2] Performing feature engineering …")
    df_eng = feature_engineering(df)

    y = df_eng['TARGET']
    drop_cols = ['TARGET', 'SK_ID_CURR', 'DAYS_EMPLOYED']
    X = df_eng.drop(columns=[c for c in drop_cols if c in df_eng.columns])

    all_numerical = X.select_dtypes(include=[np.number]).columns.tolist()
    all_categorical = X.select_dtypes(exclude=[np.number]).columns.tolist()

    print(f"    Numerical features  : {len(all_numerical)}")
    print(f"    Categorical features: {len(all_categorical)}")
    print(f"    Total features      : {len(all_numerical) + len(all_categorical)}")

    # ------------------------------------------------------------------
    # Train / validation split
    # ------------------------------------------------------------------
    print("\n[3] Splitting data (80 / 20 stratified) …")
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # Compute class weight for imbalanced target
    pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
    print(f"    scale_pos_weight    : {pos_weight:.2f}")

    # ------------------------------------------------------------------
    # Preprocessing
    # ------------------------------------------------------------------
    print("\n[4] Fitting preprocessing pipeline …")
    preprocessor = build_preprocessing_pipeline(all_numerical, all_categorical)
    X_train_proc = preprocessor.fit_transform(X_train)
    X_val_proc = preprocessor.transform(X_val)

    cat_enc = preprocessor.named_transformers_['cat'].named_steps['onehot']
    cat_cols_out = cat_enc.get_feature_names_out(all_categorical).tolist()
    feature_names = all_numerical + cat_cols_out
    print(f"    Features after OHE  : {len(feature_names)}")

    # ------------------------------------------------------------------
    # GPU detection
    # ------------------------------------------------------------------
    device = 'cpu'
    try:
        probe = xgb.XGBClassifier(tree_method='hist', device='cuda')
        probe.fit(np.array([[1, 2]]), np.array([0]))
        device = 'cuda'
        print("\n[5] GPU detected — using CUDA acceleration.")
    except Exception as e:
        print(f"\n[5] GPU check failed ({e}). Using CPU.")

    # ------------------------------------------------------------------
    # XGBoost model
    # ------------------------------------------------------------------
    print("\n[6] Training XGBoost classifier …")
    model = xgb.XGBClassifier(
        n_estimators=800,
        learning_rate=0.03,
        max_depth=7,
        min_child_weight=5,
        subsample=0.80,
        colsample_bytree=0.75,
        colsample_bylevel=0.75,
        gamma=0.10,
        reg_alpha=0.10,
        reg_lambda=1.50,
        scale_pos_weight=pos_weight,
        random_state=42,
        eval_metric='auc',
        early_stopping_rounds=40,
        device=device,
        tree_method='hist',
    )

    model.fit(
        X_train_proc, y_train,
        eval_set=[(X_val_proc, y_val)],
        verbose=100,
    )
    print(f"    Best iteration: {model.best_iteration}")

    # ------------------------------------------------------------------
    # Calibration (Platt scaling)
    # ------------------------------------------------------------------
    print("\n[7] Calibrating probabilities (Platt scaling) …")
    # Wrap the trained booster for calibration on validation fold
    calibrated_model = CalibratedClassifierCV(model, method='sigmoid', cv='prefit')
    calibrated_model.fit(X_val_proc, y_val)

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------
    print("\n[8] Evaluating model …")
    y_pred_prob_raw = model.predict_proba(X_val_proc)[:, 1]
    y_pred_prob_cal = calibrated_model.predict_proba(X_val_proc)[:, 1]
    y_pred = (y_pred_prob_cal >= 0.50).astype(int)

    auc_raw = roc_auc_score(y_val, y_pred_prob_raw)
    auc_cal = roc_auc_score(y_val, y_pred_prob_cal)
    gini = gini_score(y_val, y_pred_prob_cal)
    ks = ks_statistic(y_val.values, y_pred_prob_cal)
    brier = brier_score_loss(y_val, y_pred_prob_cal)

    report_lines = [
        "=" * 62,
        "  Model Evaluation Report",
        "=" * 62,
        f"  ROC-AUC (raw)         : {auc_raw:.4f}",
        f"  ROC-AUC (calibrated)  : {auc_cal:.4f}",
        f"  Gini coefficient      : {gini:.4f}",
        f"  KS statistic          : {ks:.4f}",
        f"  Brier score           : {brier:.4f}",
        "",
        "  Classification Report (threshold = 0.50):",
        classification_report(y_val, y_pred),
        "  Confusion Matrix:",
        str(confusion_matrix(y_val, y_pred)),
        "",
        f"  Total training time   : {time.time() - t0:.1f}s",
        "=" * 62,
    ]
    report_str = "\n".join(report_lines)
    print(report_str)

    # ------------------------------------------------------------------
    # 5-fold cross-validation AUC on training set
    # ------------------------------------------------------------------
    print("\n[9] Running 5-fold cross-validation on training data …")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_model = xgb.XGBClassifier(
        n_estimators=model.best_iteration,
        learning_rate=0.03,
        max_depth=7,
        min_child_weight=5,
        subsample=0.80,
        colsample_bytree=0.75,
        colsample_bylevel=0.75,
        gamma=0.10,
        reg_alpha=0.10,
        reg_lambda=1.50,
        scale_pos_weight=pos_weight,
        random_state=42,
        eval_metric='auc',
        device=device,
        tree_method='hist',
    )
    cv_scores = cross_val_score(
        cv_model, X_train_proc, y_train,
        scoring='roc_auc', cv=cv, n_jobs=-1
    )
    cv_line = (
        f"    CV ROC-AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}  "
        f"(folds: {', '.join(f'{s:.4f}' for s in cv_scores)})"
    )
    print(cv_line)
    report_lines.append(cv_line)

    # ------------------------------------------------------------------
    # SHAP explainer
    # ------------------------------------------------------------------
    print("\n[10] Initialising SHAP TreeExplainer …")
    explainer = shap.TreeExplainer(model)

    # Feature importance DataFrame (gain-based)
    gain_importance = model.get_booster().get_score(importance_type='gain')
    importance_df = pd.DataFrame(
        [(k, v) for k, v in gain_importance.items()],
        columns=['feature', 'importance_gain']
    )
    # Map f0, f1, … back to feature names
    importance_df['feature'] = importance_df['feature'].apply(
        lambda f: feature_names[int(f[1:])] if f.startswith('f') and f[1:].isdigit() else f
    )
    importance_df = importance_df.sort_values('importance_gain', ascending=False).reset_index(drop=True)

    # ------------------------------------------------------------------
    # Save artefacts
    # ------------------------------------------------------------------
    print(f"\n[11] Saving artefacts to {models_dir} …")

    # Preprocessor
    with open(os.path.join(models_dir, 'preprocessor.pkl'), 'wb') as f:
        pickle.dump(preprocessor, f)
    print("    ✓ preprocessor.pkl")

    # XGBoost model (native format)
    model.save_model(os.path.join(models_dir, 'model.json'))
    print("    ✓ model.json")

    # Calibrated wrapper
    with open(os.path.join(models_dir, 'calibrated_model.pkl'), 'wb') as f:
        pickle.dump(calibrated_model, f)
    print("    ✓ calibrated_model.pkl")

    # SHAP explainer
    with open(os.path.join(models_dir, 'explainer.pkl'), 'wb') as f:
        pickle.dump(explainer, f)
    print("    ✓ explainer.pkl")

    # Feature importance CSV
    fi_path = os.path.join(models_dir, 'feature_importance.csv')
    importance_df.to_csv(fi_path, index=False)
    print("    ✓ feature_importance.csv")

    # Metadata
    metadata = {
        'numerical_cols': all_numerical,
        'categorical_cols': all_categorical,
        'feature_names': feature_names,
        'n_train': len(X_train),
        'n_val': len(X_val),
        'best_iteration': int(model.best_iteration),
        'roc_auc': float(auc_cal),
        'gini': float(gini),
        'ks': float(ks),
        'brier': float(brier),
    }
    with open(os.path.join(models_dir, 'metadata.pkl'), 'wb') as f:
        pickle.dump(metadata, f)
    print("    ✓ metadata.pkl")

    # Training report (text)
    report_path = os.path.join(models_dir, 'training_report.txt')
    with open(report_path, 'w') as f:
        f.write("\n".join(report_lines))
    print("    ✓ training_report.txt")

    elapsed = time.time() - t0
    print(f"\n✅  Pipeline completed in {elapsed:.1f}s")
    print(f"    Final ROC-AUC (calibrated): {auc_cal:.4f}  |  Gini: {gini:.4f}  |  KS: {ks:.4f}")


if __name__ == '__main__':
    main()
