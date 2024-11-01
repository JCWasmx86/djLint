"""Expand html.

1. put html tags on individual lines, if needed.
2. put template tags on individual lines, if needed.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import regex as re

from ..helpers import RE_FLAGS_MX, inside_ignored_block, inside_template_block

if TYPE_CHECKING:
    from ..settings import Config


def expand_html(html: str, config: Config) -> str:
    """Split single line html into many lines based on tags."""

    def add_html_line(out_format: str, match: re.Match[str]) -> str:
        """Add whitespace.

        Do not add whitespace if the tag is in a non indent block.

        Do not add whitespace if the tag is a in a template block
        """
        if inside_ignored_block(config, html, match):
            return match.group(1)

        if inside_template_block(config, html, match):
            return match.group(1)

        if out_format == "\n%s" and match.start() == 0:
            return match.group(1)

        return out_format % match.group(1)

    add_left = partial(add_html_line, "\n%s")
    add_right = partial(add_html_line, "%s\n")

    # html tags - break before
    html = config.expand_break_before_IX.sub(add_left, html)

    # html tags - break after
    html = config.expand_break_after_IX.sub(add_right, html)

    # template tag breaks
    def should_i_move_template_tag(
        out_format: str, match: re.Match[str]
    ) -> str:
        # ensure template tag is not inside an html tag and also not the first line of the file
        if inside_ignored_block(config, html, match):
            return match.group(1)

        if not re.search(
            r"\<(?:"
            + str(config.indent_html_tags)
            # added > as not allowed inside a "" or '' to prevent invalid wild html matches
            # for issue #640
            + r")\b(?:\"[^\">]*\"|'[^'>]*'|{{[^}]*}}|{%[^%]*%}|{\#[^\#]*\#}|[^>{}])*?"
            + re.escape(match.group(1))
            + "$",
            html[: match.end()],
            flags=RE_FLAGS_MX,
        ):
            if out_format == "\n%s" and match.start() == 0:
                return match.group(1)
            return out_format % match.group(1)

        return match.group(1)

    # template tags
    # break before
    html = config.expand_template_tags_before_IMX.sub(
        partial(should_i_move_template_tag, "\n%s"), html
    )

    # break after
    return config.expand_template_tags_after_IMX.sub(
        partial(should_i_move_template_tag, "%s\n"), html
    )
