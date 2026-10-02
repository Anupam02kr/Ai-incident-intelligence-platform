import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.logs.template_miner import mine_templates, top_templates, rare_templates


def test_similar_lines_collapse_into_one_template():
    rows = [
        {"message": "PacketResponder 1 for block blk_38865049064139660 terminating"},
        {"message": "PacketResponder 2 for block blk_6952295868487656571 terminating"},
        {"message": "PacketResponder 0 for block blk_7128370237687728120 terminating"},
    ]
    tagged_rows, counts = mine_templates(rows)

    templates_seen = {r["template"] for r in tagged_rows}
    assert len(templates_seen) == 1
    assert "<*>" in list(templates_seen)[0]


def test_top_templates_orders_by_frequency():
    rows = [
        {"message": "connection reset by peer"},
        {"message": "connection reset by peer"},
        {"message": "disk quota exceeded"},
    ]
    _, counts = mine_templates(rows)
    top = top_templates(counts, n=1)

    assert top[0][1] == 2  


def test_rare_templates_below_threshold():
    rows = [
        {"message": "common thing happened"},
        {"message": "common thing happened"},
        {"message": "common thing happened"},
        {"message": "weird one-off thing"},
    ]
    _, counts = mine_templates(rows)
    rare = rare_templates(counts, threshold=1)

    assert any("weird" in tpl for tpl, _ in rare)
    assert not any("common" in tpl for tpl, _ in rare)


if __name__ == "__main__":
    from core.logs.normalizer import normalize_file

    hdfs_path = "data/raw/hdfs/HDFS_2k.log"
    if not os.path.exists(hdfs_path):
        print(f"skip: {hdfs_path} not found yet")
    else:
        rows = normalize_file(hdfs_path)
        tagged_rows, counts = mine_templates(rows)
        print(f"{len(rows)} lines -> {len(counts)} unique templates")
        print("\ntop 10:")
        for tpl, count in top_templates(counts, n=10):
            print(f"  [{count:>4}] {tpl}")
