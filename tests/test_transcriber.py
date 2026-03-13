"""Tests for transcriber download/load split."""
import unittest
from unittest.mock import patch, MagicMock


class TestGetModelSize(unittest.TestCase):
    @patch("vvrite.transcriber.model_info")
    def test_returns_size_in_bytes(self, mock_info):
        sibling = MagicMock()
        sibling.size = 600_000_000
        mock_info.return_value = MagicMock(siblings=[sibling, sibling])

        from vvrite.transcriber import get_model_size
        size = get_model_size("mlx-community/Qwen3-ASR-1.7B-8bit")
        self.assertEqual(size, 1_200_000_000)
        mock_info.assert_called_once_with("mlx-community/Qwen3-ASR-1.7B-8bit", files_metadata=True)

    @patch("vvrite.transcriber.model_info")
    def test_returns_zero_on_error(self, mock_info):
        mock_info.side_effect = Exception("network error")

        from vvrite.transcriber import get_model_size
        size = get_model_size("mlx-community/Qwen3-ASR-1.7B-8bit")
        self.assertEqual(size, 0)


class TestDownloadModel(unittest.TestCase):
    @patch("vvrite.transcriber.snapshot_download")
    def test_calls_snapshot_download(self, mock_dl):
        mock_dl.return_value = "/fake/path"

        from vvrite.transcriber import download_model
        path = download_model("test-model")
        self.assertEqual(path, "/fake/path")
        mock_dl.assert_called_once_with(repo_id="test-model")


if __name__ == "__main__":
    unittest.main()
