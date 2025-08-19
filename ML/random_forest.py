import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

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
