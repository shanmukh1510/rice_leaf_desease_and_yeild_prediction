import pickle
import matplotlib.pyplot as plt
import numpy as np

import joblib

# Load model and feature columns
with open('rice_yield_model.pkl', 'rb') as f:
    model = joblib.load(f)

with open('feature_columns.pkl', 'rb') as f:
    features = joblib.load(f)


# Ensure it's a random forest or has feature importances
if hasattr(model, 'feature_importances_'):
    importances = model.feature_importances_
    
    # Sort features by importance
    indices = np.argsort(importances)[::-1]
    
    # Plot
    plt.figure(figsize=(12, 6))
    plt.title("Random Forest Feature Importance - Yield Prediction")
    plt.bar(range(len(importances)), importances[indices], align="center", color='skyblue')
    plt.xticks(range(len(importances)), [features[i] for i in indices], rotation=45, ha='right')
    plt.xlim([-1, len(importances)])
    plt.ylabel("Importance")
    plt.xlabel("Features")
    plt.tight_layout()
    plt.savefig('rf_feature_importance.png')
    print("Feature importance graph saved as rf_feature_importance.png")
else:
    print("Model does not have feature_importances_ attribute.")
