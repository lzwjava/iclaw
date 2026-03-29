import os
import unittest

from iclaw.commands.proxy import handle_proxy_command, handle_ca_bundle_command


class TestHandleProxyCommand(unittest.TestCase):
    def test_show_current_proxy(self):
        result = handle_proxy_command("http://proxy:8080", None)
        self.assertEqual(result, "http://proxy:8080")

    def test_show_no_proxy(self):
        result = handle_proxy_command(None, None)
        self.assertIsNone(result)

    def test_set_proxy(self):
        result = handle_proxy_command(None, "http://new:1234")
        self.assertEqual(result, "http://new:1234")

    def test_set_https_proxy(self):
        result = handle_proxy_command(None, "https://secure:4321")
        self.assertEqual(result, "https://secure:4321")

    def test_clear_proxy(self):
        result = handle_proxy_command("http://old:1234", "off")
        self.assertIsNone(result)

    def test_reject_socks_proxy(self):
        result = handle_proxy_command(None, "socks5://proxy:1080")
        self.assertIsNone(result)

    def test_reject_invalid_scheme(self):
        result = handle_proxy_command(None, "ftp://proxy:21")
        self.assertIsNone(result)


class TestHandleCaBundleCommand(unittest.TestCase):
    def test_show_current_ca_bundle(self):
        result = handle_ca_bundle_command("/path/cert.pem", None)
        self.assertEqual(result, "/path/cert.pem")

    def test_show_no_ca_bundle(self):
        result = handle_ca_bundle_command(None, None)
        self.assertIsNone(result)

    def test_set_ca_bundle(self):
        # Use a file that actually exists
        path = os.path.abspath(__file__)
        result = handle_ca_bundle_command(None, path)
        self.assertEqual(result, path)

    def test_set_ca_bundle_nonexistent_file(self):
        result = handle_ca_bundle_command(None, "/nonexistent/cert.pem")
        self.assertIsNone(result)

    def test_clear_ca_bundle(self):
        result = handle_ca_bundle_command("/path/cert.pem", "off")
        self.assertIsNone(result)

    def test_set_ca_bundle_resolves_relative_path(self):
        # Use current file as a known existing file
        rel_path = os.path.relpath(__file__)
        result = handle_ca_bundle_command(None, rel_path)
        self.assertEqual(result, os.path.abspath(rel_path))


if __name__ == "__main__":
    unittest.main()
