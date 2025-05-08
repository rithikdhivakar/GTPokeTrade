# Use official Python image as base
FROM python:3.11-slim


# Set work directory inside container
WORKDIR /app

# Copy project files into the container
COPY .. /app/

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Run the application (adjust this depending on your app)
# For example, a Django app:
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
