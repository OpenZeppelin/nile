import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'src')))

from click.testing import CliRunner
from src.nile.main import cli

def test_compile():
  runner = CliRunner()
  result = runner.invoke(cli, ["compile", "--disable_hint_validation"], catch_exceptions=True)
  assert result.exit_code == 0