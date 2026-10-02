import csv
import random


CATEGORIES = [
    "Network",
    "Database",
    "Authentication",
    "Resource Exhaustion",
    "Application Error",
    "Configuration",
]

SYSTEMS = ["api-gateway", "auth-service", "order-service", "payment-service",
           "inventory-db", "user-db", "cache-node-3", "worker-7", "web-frontend"]
HOSTS = ["10.0.4.12", "10.0.4.19", "prod-app-01", "prod-app-03", "db-primary", "db-replica-2"]
PORTS = [443, 5432, 6379, 8080, 3306, 9092]

TEMPLATES = {
    "Network": [
        "Connection to {system} timed out after repeated retries from {host}.",
        "Intermittent packet loss observed between {system} and {host}, causing dropped requests.",
        "DNS resolution failed for {system}, requests falling back to stale cached IP.",
        "TLS handshake failure connecting to {host}:{port}, certificate may be expired.",
        "{system} reporting connection refused on port {port}, upstream may be down.",
        "High latency spikes on the link between {system} and {host} during peak traffic.",
        "Load balancer health checks failing for {system}, node removed from rotation.",
    ],
    "Database": [
        "{system} query latency spiking, several queries exceeding 30s on {host}.",
        "Deadlock detected in {system} transaction log, two sessions blocking each other.",
        "Replication lag on {host} growing steadily, replica falling behind primary.",
        "Connection pool exhausted for {system}, new requests queuing indefinitely.",
        "Disk I/O wait times elevated on {host}, database writes slowing down.",
        "{system} reporting too many connections, max_connections limit reached.",
        "Index corruption suspected in {system} after unexpected restart on {host}.",
        "Slow query log on {system} shows full table scans on the orders table.",
        "{system} write-ahead log growing unbounded, checkpoint process stalled.",
        "Foreign key constraint violation blocking writes to {system} on {host}.",
        "{system} autovacuum falling behind, table bloat degrading query performance.",
        "Schema migration on {system} left an index missing, queries scanning the full table.",
    ],
    "Authentication": [
        "Repeated failed login attempts for the same account on {system}, possible brute force.",
        "{system} rejecting valid tokens as expired, clock skew suspected on {host}.",
        "OAuth callback failing for {system}, redirect URI mismatch in provider config.",
        "Session tokens for {system} being invalidated prematurely after deploy.",
        "{system} returning 401 for previously working API keys, rotation may have failed.",
        "MFA verification timing out for users authenticating through {system}.",
        "Password reset emails from {system} not being delivered to users.",
    ],
    "Resource Exhaustion": [
        "{system} on {host} hit 95% memory usage before the container was OOM killed.",
        "Disk usage on {host} crossed 90%, {system} logs filling the remaining space.",
        "CPU pegged at 100% on {host}, {system} requests queuing and timing out.",
        "File descriptor limit reached on {system}, new connections being refused.",
        "Thread pool exhausted in {system}, background jobs stuck in the queue.",
        "{system} swap usage climbing steadily on {host}, performance degrading.",
        "Kubernetes evicted a pod for {system} on {host} due to memory pressure.",
    ],
    "Application Error": [
        "{system} throwing unhandled null reference exceptions on the checkout path.",
        "Deployment of {system} introduced a regression, error rate up sharply on {host}.",
        "{system} returning 500 errors intermittently after the last release.",
        "Background worker for {system} crashing repeatedly with a stack overflow.",
        "{system} serialization error when processing malformed input from a client.",
        "Race condition in {system} causing duplicate order processing under load.",
        "{system} memory leak suspected, RSS growing steadily over several hours on {host}.",
        "Unhandled exception in {system}'s webhook handler causing dropped events.",
        "{system} crashing on startup due to a missing dependency after the last deploy.",
        "Infinite retry loop in {system} client code hammering a downstream service.",
        "{system} returning malformed JSON responses since the last code change.",
        "Off-by-one bug in {system}'s pagination logic causing duplicate results.",
    ],
    "Configuration": [
        "{system} started with the wrong environment file after the last deploy.",
        "Feature flag misconfigured for {system}, rolled out to 100% instead of 5%.",
        "{system} pointing at the staging database instead of production on {host}.",
        "Missing environment variable caused {system} to fall back to default settings.",
        "{system} config reload picked up a malformed YAML file, service degraded.",
        "Incorrect timeout value in {system} config causing premature request cancellation.",
        "{system} still using the old API endpoint after the migration on {host}.",
    ],
}


def generate_incident(category, rng):
    template = rng.choice(TEMPLATES[category])
    text = template.format(
        system=rng.choice(SYSTEMS),
        host=rng.choice(HOSTS),
        port=rng.choice(PORTS),
    )
    return text


def generate_dataset(per_category=25, seed=42):
    """Returns a list of (text, category) pairs. seed is fixed by default
    so the dataset is reproducible - same data every run unless you
    deliberately change it.
    """
    rng = random.Random(seed)
    rows = []
    for category in CATEGORIES:
        seen = set()
        while len(seen) < per_category:
            text = generate_incident(category, rng)
            if text not in seen:  
                seen.add(text)
                rows.append((text, category))
    rng.shuffle(rows)
    return rows


def save_dataset(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "category"])
        writer.writerows(rows)


if __name__ == "__main__":
    rows = generate_dataset(per_category=30)
    save_dataset(rows, "eval/incident_dataset.csv")
    print(f"generated {len(rows)} incidents across {len(CATEGORIES)} categories")

    from collections import Counter
    counts = Counter(cat for _, cat in rows)
    for cat, count in counts.items():
        print(f"  {cat}: {count}")
