# GitHub Copilot Metrics Exporter

This service fetches GitHub Copilot metrics for your organization and exposes them as Prometheus metrics.

## Running with Docker

1. **Build the Docker image:**

   ```sh
   docker build -t copilot-metrics-exporter .
   ```

2. **Run the container:**

   ```sh
   docker run -d \
     -e GHC_TOKEN=your_github_copilot_token \
     -e ORG=your_github_org \
     -e CACHE_TTL_SECONDS= 3600 \
     -p 8000:8000 \
     --name copilot-metrics-exporter \
     copilot-metrics-exporter
   ```

   - Replace `your_github_copilot_token` with your GitHub Copilot API token.
   - Replace `your_github_org` with your GitHub organization name.
   - Replace `CACHE_TTL_SECONDS` with your wish of metric pull duration in seconds.

3. **Access the metrics endpoint:**

   Open [http://localhost:8000/metrics](http://localhost:8000/metrics) in your browser or Prometheus scrape config.

---

**Note:**

- The container listens on port `8000` by default.
- Make sure your GitHub token has the necessary permissions to access the Copilot metrics API.

## Metrics Documentation

Below are the Prometheus metrics exposed by this exporter, along with their descriptions and usage:

---

### 1. `copilot_exporter_requests_total`

**Type:** Counter  
**Labels:** _None_  
**Description:**  
Total number of requests made to the `/metrics` endpoint (i.e., how many times Prometheus or a user scraped metrics).

**Example:**
```
copilot_exporter_requests_total 42
```

---

### 2. `copilot_exporter_requests_failed_total`

**Type:** Counter  
**Labels:**  
- `status_code`: The HTTP status code or error type for the failure (e.g., `404`, `500`, `env_missing`, `request_exception`).

**Description:**  
Counts the number of failed or empty responses from the GitHub Copilot metrics API, labeled by the type of failure or HTTP status code.

**Example:**
```
copilot_exporter_requests_failed_total{status_code="env_missing"} 1
copilot_exporter_requests_failed_total{status_code="500"} 2
```

---

### 3. `copilot_exporter_github_api_requests`

**Type:** Counter  
**Labels:** _None_  
**Description:**  
Total number of requests made to the GitHub Copilot metrics API.

**Example:**
```
copilot_exporter_github_api_requests 40
```

---

### 4. `copilot_exporter_cache_hits`

**Type:** Counter  
**Labels:** _None_  
**Description:**  
Total number of times the cached Copilot metrics were used instead of making a new API call.

**Example:**
```
copilot_exporter_cache_hits 25
```

---

### 5. Copilot Metric Gauges

Each of the following metrics is exposed as a Prometheus Gauge with the labels:  
- `editor`
- `language`
- `stream`
- `org`

**Metric Names:**
- `total_engaged_users`
- `is_custom_model`
- `total_chat_copy_events`
- `total_chat_insertion_events`
- `total_chats`
- `total_code_acceptances`
- `total_code_lines_accepted`
- `total_code_lines_suggested`
- `total_code_suggestions`
- `total_active_users`

**Description:**  
These metrics represent various usage and engagement statistics for GitHub Copilot within your organization. Each metric is labeled by editor, language, stream, and organization for detailed analysis.

**Example:**
```
total_active_users{editor="vscode",language="python",stream="main",org="my-org"} 123
total_code_suggestions{editor="vscode",language="python",stream="main",org="my-org"} 456
```

---

## Notes

- All metrics are available at the `/metrics` endpoint.
- Use the `status_code` label on `copilot_exporter_requests_failed_total` to diagnose API or configuration issues.
- Cache hits help you monitor how often the exporter is serving data from cache versus making new API calls.
