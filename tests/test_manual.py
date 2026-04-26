import json

from kl_stadium_calendar.manual import load_manual_events
from kl_stadium_calendar.models import SourceMethod


def test_loads_manual_events(tmp_path):
    path = tmp_path / "manual_events.json"
    path.write_text(
        json.dumps(
            [
                {
                    "title": "G.E.M. I AM GLORIA",
                    "start": "2026-06-06T20:00:00+08:00",
                    "venue": "TM National Stadium Bukit Jalil",
                    "url": "https://example.test/gem",
                    "source": {
                        "id": "seed-gem",
                        "name": "Star Planet",
                        "url": "https://example.test/gem",
                        "priority": 5,
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    sources, events, reports = load_manual_events(path)

    assert sources[0].id == "seed-gem"
    assert events[0].method == SourceMethod.MANUAL
    assert events[0].start.year == 2026
    assert reports[0]["method"] == "manual"
    assert reports[0]["raw_event_count"] == 1

