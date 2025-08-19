import pandas as pd
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt

# Load the data
df = pd.read_csv("ML/matched_sensor_data.csv")
df = df[["temperature", "humidity", "soundLevel", "event"]]

# Manual mapping: fire → 1, normal → 0
df["event_encoded"] = df["event"].map({"normal": 0, "fire": 1})

# Features and target
X = df[["temperature", "humidity", "soundLevel"]]
y = df["event_encoded"]

# Train/test split (stratify to keep class ratio)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# Initialize the classifier
classifier = RandomForestClassifier(
    n_estimators=100,
    class_weight="balanced",
    random_state=42
)

# Train the model
classifier.fit(X_train, y_train)

# Predict on test set
y_pred = classifier.predict(X_test)

# Metrics
print("Classification Report:")
print(classification_report(y_test, y_pred, target_names=["normal", "fire"]))

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
# Manually define labels since no LabelEncoder was used
labels = ["normal", "fire"]

# Plot Confusion Matrix
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=labels, yticklabels=labels)

plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.tight_layout()
plt.show()


importances = classifier.feature_importances_
features = X.columns

plt.barh(features, importances)
plt.xlabel("Feature Importance")
plt.title("Random Forest Feature Importances")
plt.show()