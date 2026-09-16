from __future__ import annotations

import unittest

from app.authruntime.config import InsecureBindError, assert_safe_bind


class SafeBindTests(unittest.TestCase):
    def test_auth_enabled_allows_any_host(self) -> None:
        assert_safe_bind("0.0.0.0", auth_disabled=False)  # no raise

    def test_auth_disabled_allows_loopback(self) -> None:
        assert_safe_bind("127.0.0.1", auth_disabled=True)
        assert_safe_bind("localhost", auth_disabled=True)

    def test_auth_disabled_rejects_non_loopback(self) -> None:
        with self.assertRaises(InsecureBindError):
            assert_safe_bind("0.0.0.0", auth_disabled=True)
        with self.assertRaises(InsecureBindError):
            assert_safe_bind("192.168.1.10", auth_disabled=True)


if __name__ == "__main__":
    unittest.main()
