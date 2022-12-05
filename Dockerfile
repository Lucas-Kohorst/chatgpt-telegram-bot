FROM continuumio/miniconda3

WORKDIR /app

# Create the environment:
COPY environment.yml .
COPY requirements.txt .
COPY ./utils /app/utils/ 
COPY .env .
RUN conda env create -f environment.yml

# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "chat", "/bin/bash", "-c"]

# Activate the environment, and make sure it's activated:
RUN echo "conda activate chat" > ~/.bashrc
RUN echo "Make sure requirements.txt is installed:"
RUN pip install -r requirements.txt

RUN playwright install
RUN playwright install-deps

# The code to run when container is started:
COPY server.py .
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "chat", "python", "server.py"]

