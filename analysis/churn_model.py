import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, confusion_matrix, accuracy_score, precision_score, recall_score
url = "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"
d = pd.read_csv(url)
def bucket(s):
    h = 0
    for c in s:
        h = (h*31 + ord(c)) & 0xffffffff
    return h % 5
X = np.column_stack([np.ones(len(d)), d.tenure/72, d.MonthlyCharges/100, d.Contract.eq("Month-to-month"), d.Contract.eq("One year"), d.InternetService.eq("Fiber optic"), d.OnlineSecurity.eq("Yes"), d.TechSupport.eq("Yes")]).astype(float)
y = d.Churn.eq("Yes").to_numpy().astype(float)
test = d.customerID.map(bucket).eq(0).to_numpy()
w = np.zeros(X.shape[1])
def sigmoid(z): return 1/(1+np.exp(-z))
for _ in range(1000):
    w -= .5 * (X[~test].T @ (sigmoid(X[~test] @ w)-y[~test])) / (~test).sum()
p = sigmoid(X[test] @ w)
print("Train/test", (~test).sum(), test.sum())
print("AUC", roc_auc_score(y[test],p))
print("Confusion matrix", confusion_matrix(y[test],p>=.5))
print("Accuracy, precision, recall", accuracy_score(y[test],p>=.5),precision_score(y[test],p>=.5),recall_score(y[test],p>=.5))
