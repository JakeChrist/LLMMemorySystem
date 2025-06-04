import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from encoding import encoder


def test_encode_text_with_transformer():
    fake_model = MagicMock()
    fake_model.encode.return_value = [0.1, 0.2, 0.3]
    with patch.object(encoder, "_load_model", return_value=fake_model):
        result = encoder.encode_text("hello world")
        assert result == [0.1, 0.2, 0.3]
        fake_model.encode.assert_called_once_with("hello world")
