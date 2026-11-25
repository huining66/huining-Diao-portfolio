"""Reproducible held-out telecom churn benchmark and SHAP explanation."""
from pathlib import Path
import json
import pandas as pd
import shap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (roc_auc_score, average_precision_score, accuracy_score,
    precision_score, recall_score, confusion_matrix)
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

data = pd.read_csv("https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv")
y = data.pop("Churn").eq("Yes").astype(int)
X = pd.get_dummies(data.drop(columns=["customerID", "TotalCharges"]), dtype=float)
x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=.2, stratify=y, random_state=42)
out = Path("output"); out.mkdir(exist_ok=True)
metrics = []
models = [
    ("Logistic regression", make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))),
    ("XGBoost", XGBClassifier(n_estimators=150, max_depth=3, learning_rate=.05, random_state=42, n_jobs=2))
]
for name, model in models:
    model.fit(x_train, y_train)
    scores = model.predict_proba(x_test)[:, 1]
    labels = (scores >= .5).astype(int)
    record = {
        "model": name,
        "roc_auc": float(roc_auc_score(y_test, scores)),
        "average_precision": float(average_precision_score(y_test, scores)),
        "accuracy": float(accuracy_score(y_test, labels)),
        "precision": float(precision_score(y_test, labels, zero_division=0)),
        "recall": float(recall_score(y_test, labels, zero_division=0)),
        "tn": int(confusion_matrix(y_test, labels)[0, 0]),
        "fp": int(confusion_matrix(y_test, labels)[0, 1]),
        "fn": int(confusion_matrix(y_test, labels)[1, 0]),
        "tp": int(confusion_matrix(y_test, labels)[1, 1])
    }
    metrics.append(record)
    print(json.dumps(record))
    if name == "XGBoost":
        shap_values = shap.TreeExplainer(model)(x_test)
        shap.plots.beeswarm(shap_values, show=False)
        plt.savefig("shap_summary.png", dpi=160, bbox_inches="tight")
        plt.close("all")

pd.DataFrame(metrics).to_csv(out / "model_metrics.csv", index=False)
(out / "model_metadata.json").write_text(json.dumps({
    "total_n": len(X), "train_n": len(x_train), "test_n": len(x_test),
    "n_features_encoded": len(X.columns),
    "test_split": .2, "stratified": True, "random_state": 42,
    "evaluation": "single held-out split, no hyperparameter search",
    "dataset": "IBM sample Telco Customer Churn"
}, indent=2))
