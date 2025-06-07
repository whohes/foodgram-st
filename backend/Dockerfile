FROM python:3.13

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

# Convert script.sh to Unix line endings and make it executable
RUN sed -i 's/\r$//' script.sh && \
    chmod +x script.sh

# Use script.sh as entrypoint
ENTRYPOINT ["/bin/sh", "script.sh"]