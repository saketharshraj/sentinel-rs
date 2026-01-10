import pytest
import sentinel_rs


def test_sum_as_string():
    assert sentinel_rs.sum_as_string(1, 1) == "2"
