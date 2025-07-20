# GCP Metric Exporter for GitHub Copilot

## Overview

This project provides a containerized service to fetch GitHub Copilot metrics for your GitHub Enterprise organization and expose them as Prometheus metrics via a `/metrics` HTTP endpoint. It is designed for easy integration with Prometheus, Grafana, and other observability tools. The service can be run standalone or as part of a larger monitoring stack (e.g., with Docker Compose and Nginx reverse proxy).

## Features

- Fetches GitHub Copilot metrics using the GitHub API
- Exposes metrics in Prometheus format at `/metrics`
- Supports secure configuration via environment variables
- Ready for containerized deployment (Docker)

## Directory Structure

```
gcp-metric-exporter/
  ├── app.py              # Flask app exposing /metrics
  ├── requirements.txt    # Python dependencies
  ├── Dockerfile          # Container build file
  └── ...
```

## Prerequisites

- Python 3.9+
- Docker (for containerized deployment)
- GitHub Copilot Enterprise access
- Prometheus (for scraping metrics)

## Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd gcp-metric-exporter
```

### 2. Configure Environment Variables

```
Set the following variables in your `.env` file:
- `GHC_TOKEN`: GitHub Copilot API token (with required permissions)
- `ORG`: Your GitHub Enterprise organization name
```

### 3. Install Dependencies (for local development)

```bash
pip install -r requirements.txt
```

### 4. Run the Service

#### Locally

```bash
python app.py
```

The metrics endpoint will be available at: [http://localhost:8000/metrics](http://localhost:8000/metrics)

#### With Docker

Build and run the container:

```bash
docker build -t gcp-metric-exporter .
docker run --env-file .env -p 8000:8000 gcp-metric-exporter
```

### 5. Prometheus Configuration

Add a scrape config to your Prometheus config:

```yaml
- job_name: "gcp-metric-exporter"
  static_configs:
    - targets: ["<host>:8000"]
```

## Security

- Do not commit your real `.env` file or secrets to version control.
- Use a secure GitHub token with the minimum required permissions.

## License

MIT License

## Author

Narendranath Panda / [nks](https://naren4b.github.io/nks/)
