# official Python base image
FROM python:3.12-slim

# working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY app ./
COPY templates ./templates
COPY static ./static

# Copy trained models
COPY ML/models/rf_model.pkl ML/models/rf_model.pkl
COPY ML/models/scaler.pkl ML/models/scaler.pkl
COPY ML/models/nn_model.keras ML/models/nn_model.keras

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]