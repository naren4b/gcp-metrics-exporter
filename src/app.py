import json
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST, Counter
from flask import Flask, Response
import requests
import json
import os
import logging
import time

"""
GitHub Copilot Metrics Exporter
--------------------------------
This Flask service fetches GitHub Copilot metrics for a given organization using the GitHub API and exposes them as Prometheus metrics at /metrics.

Environment Variables:
  GHC_TOKEN: GitHub Copilot API token
  ORG: GitHub Enterprise organization name
"""

metric_names = [
    "total_engaged_users",
    "is_custom_model",
    "total_chat_copy_events",
    "total_chat_insertion_events",
    "total_chats",
    "total_code_acceptances",
    "total_code_lines_accepted",
    "total_code_lines_suggested",
    "total_code_suggestions",
    "total_active_users",
]
gauges = {
    name: Gauge(
        name,
        f"GitHub Copilot metric: {name}",
        ["editor", "language", "stream", "org"],
    )
    for name in metric_names
}

# Add a counter for failed or empty responses with status_code label
failed_metrics_counter = Counter(
    "copilot_exporter_requests_failed_total",
    "Number of failed or empty responses from get_copilot_metrics",
    ["status_code"],
)

# Add a counter for total requests to /metrics
total_request_counter = Counter(
    "copilot_exporter_requests_total", "Total number of requests to get_copilot_metrics"
)

# Total number of requests to Github metrics Api
total_github_api_request_counter = Counter(
    "copilot_exporter_github_api_requests",
    "Total number of requests to Github metrics Api",
)
# Total number of cache hits for get_copilot_metrics
total_cache_hit_counter = Counter(
    "copilot_exporter_cache_hits", "Total number of cache hits for get_copilot_metrics"
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_copilot_metrics(GHC_TOKEN, ORG):
    """
    Fetch the latest GitHub Copilot metrics for the given organization using the GitHub API.
    Args:
        GHC_TOKEN (str): GitHub Copilot API token.
        ORG (str): GitHub Enterprise organization name.
    Returns:
        dict: Latest Copilot metrics for the organization.
    Raises:
        EnvironmentError: If GHC_TOKEN or ORG is not set.
    """
    total_github_api_request_counter.inc()  # Increment total GitHub API request counter
    if not GHC_TOKEN or not ORG:
        logger.error("GHC_TOKEN and ORG environment variables must be set.")
        failed_metrics_counter.labels(status_code="env_missing").inc()
        raise EnvironmentError("GHC_TOKEN and ORG environment variables must be set.")

    logger.info("Fetching GitHub Copilot metrics...")
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GHC_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    url = f"https://api.github.com/enterprises/{ORG}/copilot/metrics"
    logger.info(f"Fetching metrics from {url} for organization {ORG}")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        status_code = getattr(e.response, "status_code", "http_error")
        logger.error(f"HTTP error fetching metrics: {e}")
        failed_metrics_counter.labels(status_code=str(status_code)).inc()
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching metrics: {e}")
        failed_metrics_counter.labels(status_code="request_exception").inc()
        return {}

    try:
        data = response.json()
    except ValueError:
        logger.error("Response content is not valid JSON.")
        failed_metrics_counter.labels(status_code=str(response.status_code)).inc()
        return {}

    if not data:
        failed_metrics_counter.labels(status_code=str(response.status_code)).inc()

    latest_data = data[-1] if isinstance(data, list) and data else data
    latest_org_data = {"org": ORG}
    latest_org_data.update(latest_data)
    logger.info(
        f"Fetched {len(data) if isinstance(data, list) else 1} entries for organization {ORG}"
    )
    logger.debug(
        f"Latest data for organization {ORG}: {json.dumps(latest_org_data, indent=2)}"
    )
    return latest_org_data


def collect_metrics(data):
    """
    Flatten and extract relevant Copilot metrics from the nested API response.
    Args:
        data (dict): Copilot metrics JSON from the API.
    Returns:
        list: List of metric rows (dicts) with labels and values.
    """
    metrics = [
        "total_engaged_users",
        "is_custom_model",
        "total_chat_copy_events",
        "total_chat_insertion_events",
        "total_chats",
        "total_code_acceptances",
        "total_code_lines_accepted",
        "total_code_lines_suggested",
        "total_code_suggestions",
        "total_active_users",
    ]
    rows = []

    # Top-level metrics
    for key in ["copilot_dotcom_chat", "copilot_dotcom_pull_requests"]:
        if key in data:
            for m in metrics:
                if m in data[key]:
                    rows.append(
                        {
                            "metric_parent": key,
                            "editor": "",
                            "language": "",
                            "metric": m,
                            "value": data[key][m],
                        }
                    )

    # copilot_ide_chat
    if "copilot_ide_chat" in data:
        parent = "copilot_ide_chat"
        if "total_engaged_users" in data[parent]:
            rows.append(
                {
                    "metric_parent": parent,
                    "editor": "",
                    "language": "",
                    "metric": "total_engaged_users",
                    "value": data[parent]["total_engaged_users"],
                }
            )
        for editor in data[parent].get("editors", []):
            editor_name = editor.get("name", "")
            if "total_engaged_users" in editor:
                rows.append(
                    {
                        "metric_parent": parent,
                        "editor": editor_name,
                        "language": "",
                        "metric": "total_engaged_users",
                        "value": editor["total_engaged_users"],
                    }
                )
            for model in editor.get("models", []):
                if "is_custom_model" in model:
                    rows.append(
                        {
                            "metric_parent": parent,
                            "editor": editor_name,
                            "language": "",
                            "metric": "is_custom_model",
                            "value": model["is_custom_model"],
                        }
                    )
                for m in [
                    "total_chat_copy_events",
                    "total_chat_insertion_events",
                    "total_chats",
                    "total_engaged_users",
                ]:
                    if m in model:
                        rows.append(
                            {
                                "metric_parent": parent,
                                "editor": editor_name,
                                "language": "",
                                "metric": m,
                                "value": model[m],
                            }
                        )

    # copilot_ide_code_completions
    if "copilot_ide_code_completions" in data:
        parent = "copilot_ide_code_completions"
        if "total_engaged_users" in data[parent]:
            rows.append(
                {
                    "metric_parent": parent,
                    "editor": "",
                    "language": "",
                    "metric": "total_engaged_users",
                    "value": data[parent]["total_engaged_users"],
                }
            )
        for editor in data[parent].get("editors", []):
            editor_name = editor.get("name", "")
            if "total_engaged_users" in editor:
                rows.append(
                    {
                        "metric_parent": parent,
                        "editor": editor_name,
                        "language": "",
                        "metric": "total_engaged_users",
                        "value": editor["total_engaged_users"],
                    }
                )
            for model in editor.get("models", []):
                if "is_custom_model" in model:
                    rows.append(
                        {
                            "metric_parent": parent,
                            "editor": editor_name,
                            "language": "",
                            "metric": "is_custom_model",
                            "value": model["is_custom_model"],
                        }
                    )
                if "total_engaged_users" in model:
                    rows.append(
                        {
                            "metric_parent": parent,
                            "editor": editor_name,
                            "language": "",
                            "metric": "total_engaged_users",
                            "value": model["total_engaged_users"],
                        }
                    )
                for lang in model.get("languages", []):
                    lang_name = lang.get("name", "")
                    for m in [
                        "total_code_acceptances",
                        "total_code_lines_accepted",
                        "total_code_lines_suggested",
                        "total_code_suggestions",
                        "total_engaged_users",
                    ]:
                        if m in lang:
                            rows.append(
                                {
                                    "metric_parent": parent,
                                    "editor": editor_name,
                                    "language": lang_name,
                                    "metric": m,
                                    "value": lang[m],
                                }
                            )
        # language summary
        for lang in data[parent].get("languages", []):
            lang_name = lang.get("name", "")
            if "total_engaged_users" in lang:
                rows.append(
                    {
                        "metric_parent": parent,
                        "editor": "",
                        "language": lang_name,
                        "metric": "total_engaged_users",
                        "value": lang["total_engaged_users"],
                    }
                )

    # Top-level totals
    for m in ["total_active_users", "total_engaged_users"]:
        if m in data:
            rows.append(
                {
                    "metric_parent": "",
                    "editor": "",
                    "language": "",
                    "metric": m,
                    "value": data[m],
                }
            )

    return rows


def update_metrics(org, data):
    """
    Update Prometheus Gauge metrics with the latest Copilot metrics for the given org.
    Args:
        org (str): Organization name.
        data (dict): Copilot metrics for the org.
    """
    rows = []
    org_rows = collect_metrics(data)
    for row in org_rows:
        row["org"] = org
    rows.extend(org_rows)

    # Set metric values
    for row in rows:
        metric = row["metric"]
        if metric in gauges:
            gauges[metric].labels(
                editor=row.get("editor", "") or "",
                language=row.get("language", "") or "",
                stream=row.get("metric_parent", "") or "",
                org=row.get("org", "") or "",
            ).set(row["value"])


# Flask app for /metrics endpoint
app = Flask(__name__)


copilot_metrics_cache = {"timestamp": 0, "data": None}
CACHE_TTL_SECONDS = int(os.environ.get(
    "CACHE_TTL_SECONDS", 4 * 60 * 60
))  # Default to 4 hours if not set


@app.route("/metrics")
def metrics():
    """
    HTTP GET /metrics
    Fetches the latest Copilot metrics from GitHub, updates Prometheus metrics, and returns them.
    Returns:
        Response: Prometheus metrics exposition format.
    """
    total_request_counter.inc()  # Increment total request counter
    GHC_TOKEN = os.environ.get("GHC_TOKEN")
    ORG = os.environ.get("ORG")
    now = time.time()
    if (
        copilot_metrics_cache["data"] is not None
        and (now - copilot_metrics_cache["timestamp"]) < CACHE_TTL_SECONDS
    ):
        logger.info("Returning Copilot metrics from cache.")
        data = copilot_metrics_cache["data"]
        total_cache_hit_counter.inc()
    else:
        data = get_copilot_metrics(GHC_TOKEN, ORG)
        copilot_metrics_cache["data"] = data
        copilot_metrics_cache["timestamp"] = now
    update_metrics(ORG, data)
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route("/test_metrics")
def test_metrics():
    total_request_counter.inc()
    failed_metrics_counter.labels(status_code="test").inc()
    return "Test metrics incremented"


if __name__ == "__main__":
    print("Starting Flask server on port 8000 with /metrics endpoint")
    app.run(host="0.0.0.0", port=8000)
