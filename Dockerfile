FROM python:3.10-slim

# Suppress pip root user warning
ENV PIP_ROOT_USER_ACTION=ignore

RUN apt-get update && apt-get install -y git build-essential

WORKDIR /app

COPY . .

# Install dependencies from pyproject.toml and explicitly install streamlit
# We use pip install . to install the current package and its dependencies
RUN pip install --no-cache-dir -e . && \
    pip install --no-cache-dir streamlit

# Expose Streamlit port
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
