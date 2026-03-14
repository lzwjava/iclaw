import unittest
from unittest.mock import MagicMock, patch
from iclaw import login

class TestLogin(unittest.TestCase):
    @patch("iclaw.login.requests.post")
    def test_login_flow(self, mock_post):
        mock_post.return_value = MagicMock(ok=True, json=lambda: {"device_code": "dc", "user_code": "uc", "verification_uri": "v"})
        self.assertEqual(login.get_device_code()["device_code"], "dc")
        
        mock_post.side_effect = [MagicMock(ok=True, json=lambda: {"access_token": "at"})]
        with patch("iclaw.login.time.sleep"):
            self.assertEqual(login.poll_for_access_token("dc", 1), "at")

if __name__ == "__main__":
    unittest.main()
