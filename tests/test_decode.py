from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pidbox.io.decode import decode_blackbox


class _StubParser:
    def __init__(self, sessions, field_names):
        self._sessions = sessions
        self._current_index = 0
        self.field_names = field_names
        self.reader = SimpleNamespace(log_count=len(sessions))

    def set_log_index(self, index: int):
        self._current_index = index - 1

    def frames(self):
        for row in self._sessions[self._current_index]:
            yield SimpleNamespace(data=tuple(row))


class DecodeBlackboxTest(unittest.TestCase):
    def test_decode_blackbox_creates_csvs_for_each_session(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            log_path = tmp_path / "flight.bbl"
            log_path.write_bytes(b"stub")

            field_names = ["time", "gyroADC[0]"]
            sessions = [
                [(1, 10)],
                [(2, 20), (3, 30)],
            ]
            stub_parser = _StubParser(sessions=sessions, field_names=field_names)

            with patch("pidbox.io.decode.Parser") as parser_cls:
                parser_cls.load.return_value = stub_parser
                decoder_used, csv_paths = decode_blackbox(log_path, project_root=tmp_path)

            self.assertEqual(decoder_used, "orangebox")
            self.assertEqual([p.name for p in csv_paths], ["flight_001.csv", "flight_002.csv"])

            first_df = pd.read_csv(csv_paths[0])
            second_df = pd.read_csv(csv_paths[1])

            self.assertListEqual(list(first_df.columns), field_names)
            self.assertListEqual(first_df.iloc[0].tolist(), [1, 10])
            self.assertListEqual(second_df.iloc[-1].tolist(), [3, 30])
