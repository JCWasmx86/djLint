"""Djlint tests specific to html.

run::

   pytest tests/test_html.py --cov=src/djlint --cov-branch \
          --cov-report xml:coverage.xml --cov-report term-missing

   pytest tests/test_html.py::test_front_matter --cov=src/djlint --cov-branch \
          --cov-report xml:coverage.xml --cov-report term-missing


"""
# pylint: disable=C0116
from typing import TextIO

from click.testing import CliRunner

from tests.conftest import reformat


def test_hr_tag(runner: CliRunner, tmp_file: TextIO) -> None:
    output = reformat(
        tmp_file,
        runner,
        b"""<div>
    <div>
        <hr>
    </div>
</div>
""",
    )
    assert output.exit_code == 0

    output = reformat(
        tmp_file,
        runner,
        b"""<div>
    <div>
        <hr />
    </div>
</div>
""",
    )

    assert output.exit_code == 0
