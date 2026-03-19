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


class TestWarmUp(unittest.TestCase):
    @patch("vvrite.transcriber.os.unlink")
    @patch("vvrite.transcriber._create_warmup_audio", return_value="/tmp/warmup.wav")
    def test_warm_up_runs_single_dummy_generate(self, mock_audio, mock_unlink):
        import vvrite.transcriber as transcriber

        model = MagicMock()
        old_model = transcriber._model
        old_warmed_up = transcriber._warmed_up
        try:
            transcriber._model = model
            transcriber._warmed_up = False

            transcriber.warm_up()

            model.generate.assert_called_once_with("/tmp/warmup.wav", max_tokens=1)
            mock_unlink.assert_called_once_with("/tmp/warmup.wav")
            self.assertTrue(transcriber._warmed_up)
        finally:
            transcriber._model = old_model
            transcriber._warmed_up = old_warmed_up

    @patch("vvrite.transcriber._safe_warm_up")
    @patch("vvrite.transcriber.load_model", return_value=MagicMock())
    def test_load_from_local_triggers_warm_up(self, mock_load_model, mock_safe_warm_up):
        from vvrite.transcriber import load_from_local

        load_from_local("/tmp/model")

        mock_load_model.assert_called_once_with("/tmp/model")
        mock_safe_warm_up.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
