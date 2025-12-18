# Use full Python image which includes build tools (gcc, etc.)
# This avoids the need for apt-get update/install which was failing
FROM python:3.10

# Suppress pip root user warning
ENV PIP_ROOT_USER_ACTION=ignore
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
