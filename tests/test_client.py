import os
import unittest.mock

import pytest

from yahoo_data import client


def test_fetch_json_without_credentials_raises_before_any_network_call():
    env_without_yahoo_vars = {
        key: value for key, value in os.environ.items() if not key.startswith("YAHOO_")
    }
    with unittest.mock.patch.dict(os.environ, env_without_yahoo_vars, clear=True):
        with unittest.mock.patch("urllib.request.urlopen") as urlopen:
            with pytest.raises(client.YahooCredentialsError):
                client.fetch_json("/league/000.l.1/players;status=A")
            urlopen.assert_not_called()
