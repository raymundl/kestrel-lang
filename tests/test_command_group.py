import json
import logging
import os
import pytest
import pathlib
import shutil
import tempfile
import pandas as pd

from kestrel.session import Session


@pytest.fixture
def fake_bundle_file():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "test_bundle.json")


def test_group_srcref(fake_bundle_file):
    with Session(debug_mode=True) as session:
        session.execute(
            f"""conns = get network-traffic
            from file://{fake_bundle_file}
            where [network-traffic:dst_port > 0]""",
        )

        session.execute("src_grps = group conns by network-traffic:src_ref.value")
        assert "src_grps" in session.get_variable_names()
        src_grps = session.get_variable("src_grps")
        assert src_grps is not None


def test_group_src_dst(fake_bundle_file):
    with Session(debug_mode=True) as session:
        session.execute(
            f"""conns = get network-traffic
            from file://{fake_bundle_file}
            where [network-traffic:dst_port > 0]""",
        )

        session.execute(("grps = group conns by "
                         "network-traffic:src_ref.value,"
                         "network-traffic:dst_ref.value"))
        assert "grps" in session.get_variable_names()
        grps = session.get_variable("grps")
        assert grps is not None


@pytest.mark.parametrize(
    "agg_func, attr, expected",
    [
        ("sum", "number_observed", "sum_number_observed"),
        ("avg", "number_observed", "avg_number_observed"),
        ("min", "last_observed", "min_last_observed"),
        ("max", "dst_ref.value", "max_dst_ref.value"),
        ("count", "dst_ref.value", "count_dst_ref.value"),
        ("nunique", "dst_ref.value", "nunique_dst_ref.value"),
    ]
)
def test_group_srcref_agg(fake_bundle_file, agg_func, attr, expected):
    with Session(debug_mode=True) as session:
        session.execute(
            f"""conns = get network-traffic
            from file://{fake_bundle_file}
            where [network-traffic:dst_port > 0]""",
        )

        session.execute(("src_grps = group conns by network-traffic:src_ref.value"
                         f" with {agg_func}({attr})"))
        assert "src_grps" in session.get_variable_names()
        src_grps = session.get_variable("src_grps")
        assert src_grps is not None
        assert expected in src_grps[0]


@pytest.mark.parametrize(
    "agg_func, attr, alias",
    [
        ("sum", "number_observed", "count"),
        ("avg", "number_observed", "avg_count"),
        ("min", "last_observed", "foo"),
        ("max", "dst_ref.value", "rand_value"),
        ("count", "dst_ref.value", "whatever"),
        ("nunique", "dst_ref.value", "unique_dests"),
    ]
)
def test_group_srcref_agg_alias(fake_bundle_file, agg_func, attr, alias):
    with Session(debug_mode=True) as session:
        session.execute(
            f"""conns = get network-traffic
            from file://{fake_bundle_file}
            where [network-traffic:dst_port > 0]""",
        )

        session.execute(("src_grps = group conns by network-traffic:src_ref.value"
                         f" with {agg_func}({attr}) as {alias}"))
        assert "src_grps" in session.get_variable_names()
        src_grps = session.get_variable("src_grps")
        assert src_grps is not None
        assert alias in src_grps[0]
