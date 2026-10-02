from collections import Counter

from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig

def build_miner(persistence_path=None):
    config = TemplateMinerConfig()
    config.load_defaults = True

    if persistence_path:
        from drain3.file_persistence import FilePersistence
        persistence = FilePersistence(persistence_path)
    else:
        persistence = None

    return TemplateMiner(persistence_handler=persistence, config=config)


def mine_templates(rows, persistence_path=None):
    
    miner = build_miner(persistence_path)
    tagged_rows = []

    for row in rows:
        result = miner.add_log_message(row["message"])
        tagged = dict(row)
        tagged["template_id"] = result["cluster_id"]
        tagged_rows.append(tagged)

    final_template_by_id = {c.cluster_id: c.get_template() for c in miner.drain.clusters}
    for tagged in tagged_rows:
        tagged["template"] = final_template_by_id[tagged["template_id"]]

    template_counts = Counter(r["template"] for r in tagged_rows)

    return tagged_rows, template_counts


def top_templates(template_counts, n=10):
    return template_counts.most_common(n)


def rare_templates(template_counts, threshold=3):
    return [(tpl, count) for tpl, count in template_counts.items() if count <= threshold]


if __name__ == "__main__":
    import sys
    import os

    sys.path.insert(0, os.path.dirname(__file__))
    from normalizer import normalize_file

    hdfs_path = "../../data/raw/hdfs/HDFS_2k.log"

    if not os.path.exists(hdfs_path):
        print(f"skip: {hdfs_path} not found, run this from core/logs/ or adjust the path")
    else:
        rows = normalize_file(hdfs_path)
        tagged_rows, counts = mine_templates(rows)

        print(f"{len(rows)} lines -> {len(counts)} unique templates\n")

        print("top 5 templates:")
        for tpl, count in top_templates(counts, n=5):
            print(f"  [{count:>4}] {tpl}")

        print("\nrare templates (<=3 occurrences):")
        for tpl, count in rare_templates(counts, threshold=3):
            print(f"  [{count:>4}] {tpl}")
