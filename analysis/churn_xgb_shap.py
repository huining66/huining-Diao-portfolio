"""Experimental model comparison; run to obtain results."""
import pandas as pd
import shap
import matplotlib.pyplot as plt
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score,average_precision_score
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
d=pd.read_csv("https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv")
y=d.pop("Churn").eq("Yes").astype(int)
X=pd.get_dummies(d.drop(columns=["customerID","TotalCharges"]),dtype=float)
a,b,c,e=train_test_split(X,y,test_size=.2,stratify=y,random_state=42)
for model in [make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000)),XGBClassifier(n_estimators=150,max_depth=3,learning_rate=.05,random_state=42,n_jobs=2)]:
    model.fit(a,c)
    p=model.predict_proba(b)[:,1]
    print(type(model).__name__,roc_auc_score(e,p),average_precision_score(e,p))
    if isinstance(model,XGBClassifier):
        values=shap.TreeExplainer(model)(b)
        shap.plots.beeswarm(values,show=False)
        plt.savefig("shap_summary.png",dpi=160,bbox_inches="tight")
