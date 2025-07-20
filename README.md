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
     -p 8000:8000 \
     copilot-metrics-exporter
   ```

   - Replace `your_github_copilot_token` with your GitHub Copilot API token.
   - Replace `your_github_org` with your GitHub organization name.

3. **Access the metrics endpoint:**

   Open [http://localhost:8000/metrics](http://localhost:8000/metrics) in your browser or Prometheus scrape config.

---

**Note:**  
- The container listens on port `8000` by default.
- Make sure your GitHub token
