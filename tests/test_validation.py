from dataclasses import asdict
import json
import pytest
from radio.core import Broadcaster, load_stations, parse_stations


def test_windows_utf8_bom_configuration(tmp_path):
    path = tmp_path / "stations.json"
    expected = load_stations()
    path.write_text(json.dumps([asdict(s) for s in expected]), encoding="utf-8-sig")
    assert load_stations(path) == expected


@pytest.mark.parametrize("items", [None, {}, [], ["channel"], [{"id": 1}]])
def test_invalid_station_lists(items):
    with pytest.raises(ValueError):
        parse_stations(items)


@pytest.mark.parametrize("field,value", [("name", None), ("description", 5),
                                        ("source", ""), ("source", []),
                                        ("group", None)])
def test_invalid_station_field_types(field, value):
    item = asdict(load_stations()[0])
    item[field] = value
    with pytest.raises(ValueError):
        parse_stations([item])


def test_duplicate_remote_station_ids():
    items = [asdict(station) for station in load_stations()]
    items[1]["id"] = items[0]["id"]
    with pytest.raises(ValueError, match="unique IDs"):
        parse_stations(items)


def test_failed_process_start_releases_membership(monkeypatch):
    import radio.core as core
    def fail(*args, **kwargs):
        raise OSError("Simulated process launch failure")
    monkeypatch.setattr(core.subprocess, "Popen", fail)
    broadcaster = Broadcaster()
    try:
        with pytest.raises(OSError, match="Simulated"):
            broadcaster.start(load_stations()[0], "127.0.0.1")
        assert not broadcaster.memberships
        assert not broadcaster.processes
    finally:
        broadcaster.stop()
