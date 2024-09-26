# Use the lightweight Python Alpine image
FROM python:3.12-alpine

# Set the working directory
WORKDIR /app

# Copy requirements file
COPY /app/requirements.txt .

# Install FastAPI and Uvicorn
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the application port
EXPOSE 8000

# Command to run the FastAPI application
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]
