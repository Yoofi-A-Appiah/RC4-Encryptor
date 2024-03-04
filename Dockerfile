# Define a build argument for the wheel distribution directory
ARG WHEEL_DIST="/tmp/wheels"

# Stage 1: Build dependencies
FROM python:3.8-slim-bullseye as builder

# Define the wheel distribution directory as a build argument
ARG WHEEL_DIST

# Install build dependencies
RUN apt-get update && \
    apt-get install -y gcc g++ unixodbc-dev

# Copy the requirements file to the temporary directory
COPY requirements.txt /tmp/requirements.txt

# Generate wheel packages for the requirements
RUN python3 -m pip wheel -w "${WHEEL_DIST}" -r /tmp/requirements.txt


# Stage 2: Create a smaller image
FROM python:3.8-slim-bullseye

# Define the wheel distribution directory as a build argument
ARG WHEEL_DIST

# Copy the wheel distribution from the builder stage
COPY --from=builder "${WHEEL_DIST}" "${WHEEL_DIST}"

# Set the working directory
WORKDIR /app

# Install the dependencies from the wheel distribution
RUN pip3 --no-cache-dir install "${WHEEL_DIST}"/*.whl

# Copy your app into the container
COPY src/ /app/src

ENV FLASK_APP=src.app

EXPOSE 8000

# Define the command to run your app
CMD ["flask", "run", "--host=0.0.0.0", "--port", "8000"]