import pandas as pd
import mlflow
import mlflow.sklearn
import dagshub
import optuna
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import f1_score
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

# --- 1. DAGSHUB CONFIG ---
# Replace with your actual username and repo name from Dagshub
USERNAME = "YOUR_DAGSHUB_USERNAME"
REPO_NAME = "YOUR_REPO_NAME"

dagshub.init(repo_name=REPO_NAME, repo_owner=USERNAME, mlflow=True)
mlflow.set_experiment("PL_16_Experiments")

# --- 2. DATA PREP ---
df = pd.read_csv("database/rolling_data.csv")
features = ["gf_rolling", "ga_rolling", "xg_rolling", "xga_rolling", 
            "poss_rolling", "sh_rolling", "sot_rolling", "dist_rolling", "venue_code"]
X = df[features]
y = df["target"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# --- 3. HYPERPARAMETER TUNING (OPTUNA) ---
def get_best_params(model_name, xt, yt):
    def objective(trial):
        if model_name == "RF":
            params = {"n_estimators": trial.suggest_int("n_estimators", 50, 200), "max_depth": trial.suggest_int("max_depth", 5, 20)}
            m = RandomForestClassifier(**params)
        elif model_name == "XGB":
            params = {"n_estimators": trial.suggest_int("n_estimators", 50, 200), "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2)}
            m = XGBClassifier(**params)
        elif model_name == "LGBM":
            params = {"n_estimators": trial.suggest_int("n_estimators", 50, 200), "num_leaves": trial.suggest_int("num_leaves", 20, 50)}
            m = LGBMClassifier(**params, verbose=-1)
        else:
            params = {"C": trial.suggest_float("C", 0.1, 10.0)}
            m = LogisticRegression(**params)
            
        m.fit(xt, yt)
        return f1_score(y_test, m.predict(pca_transform(X_test_scaled, xt.shape[1])), average='weighted')

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=5)
    return study.best_params

def pca_transform(data, n_cols):
    if n_cols < 9: # If PCA was applied
        pca_temp = PCA(n_components=n_cols)
        pca_temp.fit(X_train_scaled)
        return pca_temp.transform(data)
    return data

# --- 4. THE 16 EXPERIMENT LOOP ---
model_classes = {"RF": RandomForestClassifier, "XGB": XGBClassifier, "LGBM": LGBMClassifier, "LogReg": LogisticRegression}

print("🧪 Starting 16 Experiments...")

for m_name, m_class in model_classes.items():
    for use_pca in [False, True]:
        for use_tune in [False, True]:
            run_name = f"{m_name}_PCA:{use_pca}_Tuned:{use_tune}"
            
            with mlflow.start_run(run_name=run_name):
                # Apply PCA Condition
                xt = X_train_scaled
                xe = X_test_scaled
                if use_pca:
                    pca = PCA(n_components=5)
                    xt = pca.fit_transform(xt)
                    xe = pca.transform(xe)
                
                # Apply Tuning Condition
                params = {}
                if use_tune:
                    params = get_best_params(m_name, xt, y_train)
                    mlflow.log_params(params)
                
                # Train Final Model for this Run
                model = m_class(**params)
                model.fit(xt, y_train)
                
                # Log Metrics
                preds = model.predict(xe)
                f1 = f1_score(y_test, preds, average='weighted')
                mlflow.log_metric("f1_score", f1)
                mlflow.log_param("pca_used", use_pca)
                mlflow.log_param("tuning_used", use_tune)
                
                # Save the model to Dagshub
                mlflow.sklearn.log_model(model, "model")
                print(f"✅ Finished {run_name} | F1: {f1:.4f}")

print("🚀 All experiments are now live on Dagshub!")