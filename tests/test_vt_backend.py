"""No-network tests for the server-mediated VT lookup without a client key."""
import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from src import vt_backend as vt
from src.mod_security import VirusTotalError


class Response(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *a):
        self.close()


class VTBackendTests(unittest.TestCase):
    def setUp(self):
        self.digest = "a" * 64
        self.token = "x" * 64

    def test_requires_registered_device(self):
        with patch("src.vt_backend._load_token", return_value=None):
            with self.assertRaisesRegex(VirusTotalError, "аккаунт"):
                vt.lookup_shared_vt_hash(self.digest)

    def test_rejects_bad_digest_before_network(self):
        with patch("src.vt_backend._load_token", return_value=self.token):
            with self.assertRaisesRegex(VirusTotalError, "SHA-256"):
                vt.lookup_shared_vt_hash("../../evil")

    def test_uses_only_hash_and_protected_pairing_token(self):
        payload = {
            "known": True, "sha256": self.digest,
            "malicious": 0, "suspicious": 1,
            "harmless": 10, "undetected": 57
        }
        mock_opener = unittest.mock.Mock()
        mock_opener.open.return_value = Response(json.dumps(payload).encode("utf-8"))
        with patch("src.vt_backend._load_token", return_value=self.token):
            with patch("src.vt_backend.build_opener", return_value=mock_opener):
                report = vt.lookup_shared_vt_hash(self.digest)
        self.assertEqual(report["suspicious"], 1)
        request = mock_opener.open.call_args.args[0]
        request_body = json.loads(request.data)
        self.assertEqual(set(request_body), {"sha256", "device_token"})
        self.assertEqual(request_body["sha256"], self.digest)
        self.assertEqual(request_body["device_token"], self.token)
        self.assertEqual(request.full_url, vt.ENDPOINT)
        self.assertNotIn(b"x-apikey", request.data)

    def test_handles_unlinked_account(self):
        opener = unittest.mock.Mock()
        opener.open.side_effect = HTTPError(vt.ENDPOINT, 401, "missing", {}, None)
        with patch("src.vt_backend._load_token", return_value=self.token):
            with patch("src.vt_backend.build_opener", return_value=opener):
                with self.assertRaisesRegex(VirusTotalError, "Аккаунт"):
                    vt.lookup_shared_vt_hash(self.digest)

    def test_rejects_server_report_with_different_digest(self):
        response = Response(json.dumps({
            "known": True, "sha256": "0" * 64,
            "malicious": 0, "suspicious": 0,
            "harmless": 0, "undetected": 1
        }).encode("utf-8"))
        opener = unittest.mock.Mock()
        opener.open.return_value = response
        with patch("src.vt_backend._load_token", return_value=self.token):
            with patch("src.vt_backend.build_opener", return_value=opener):
                with self.assertRaisesRegex(VirusTotalError, "некорректный"):
                    vt.lookup_shared_vt_hash(self.digest)


if __name__ == "__main__":
    unittest.main()
