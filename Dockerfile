# Use the official Python image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Expose port
EXPOSE 8080

# Command to run the app
CMD ["python", "app.py"]
