EVAL_QUERIES = [
    ("DataNode keeps terminating blocks, might be a bad disk", "runbook_disk_failure.md"),
    ("how to check if a hard drive is failing", "runbook_disk_failure.md"),

    ("requests hanging waiting for a database connection", "runbook_connection_pool.md"),
    ("too many idle connections open on postgres", "runbook_connection_pool.md"),

    ("lots of failed ssh logins from the same ip", "runbook_brute_force.md"),
    ("someone might be trying to brute force our login page", "runbook_brute_force.md"),

    ("container got killed with no error in the app logs", "runbook_oom_killer.md"),
    ("process memory usage climbing until it crashes", "runbook_oom_killer.md"),

    ("error rate jumped right after we shipped a new release", "runbook_deploy_regression.md"),
    ("should we roll back after a bad deploy", "runbook_deploy_regression.md"),

    ("service acting weird after deploy but no code changed", "runbook_config_drift.md"),
    ("feature flag accidentally enabled for everyone", "runbook_config_drift.md"),

    ("api calls between two services timing out randomly", "runbook_network_timeout.md"),
    ("packet loss between application servers", "runbook_network_timeout.md"),

    ("service stopped accepting new work but isn't using much cpu", "runbook_thread_exhaustion.md"),
    ("too many open files error", "runbook_thread_exhaustion.md"),

    ("valid auth tokens being rejected as expired", "runbook_oauth_config.md"),
    ("oauth redirect uri not matching", "runbook_oauth_config.md"),

    ("no space left on device error writing to disk", "runbook_disk_space.md"),
    ("logs filling up the whole disk", "runbook_disk_space.md"),
]


if __name__ == "__main__":
    print(f"{len(EVAL_QUERIES)} evaluation queries across "
          f"{len(set(source for _, source in EVAL_QUERIES))} runbooks")
