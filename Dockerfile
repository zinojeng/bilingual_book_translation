FROM python:3.10-slim

# Suppress pip root user warning
ENV PIP_ROOT_USER_ACTION=ignore

RUN apt-get update && apt-get install -y git build-essential

WORKDIR /app

# Install PDM
RUN pip install pdm

# Copy dependency files
COPY pyproject.toml pdm.lock ./

# Install dependencies using PDM (excluding the project itself for now to cache dependencies)
RUN pdm config python.use_venv false && \
    pdm install --prod --no-editable --no-self

# Copy the rest of the application
COPY . .

# Install the project itself and streamlit
RUN pdm install --prod --no-editable && \
    pip install --no-cache-dir streamlit

# Expose Streamlit port
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
