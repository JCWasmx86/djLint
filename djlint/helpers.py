"""Collection of shared djLint functions."""
# ruff: noqa: ERA001

from __future__ import annotations

import itertools
from functools import cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final

    from .settings import Config

import regex as re

RE_FLAGS_IS: Final = re.I | re.S
RE_FLAGS_IX: Final = re.I | re.X
RE_FLAGS_MS: Final = re.M | re.S
RE_FLAGS_MX: Final = re.M | re.X
RE_FLAGS_IMS: Final = re.I | re.M | re.S
RE_FLAGS_IMX: Final = re.I | re.M | re.X
RE_FLAGS_ISX: Final = re.I | re.S | re.X
RE_FLAGS_IMSX: Final = re.I | re.M | re.S | re.X


def is_ignored_block_opening(config: Config, item: str) -> bool:
    """Find ignored group opening.

    A valid ignored group opening tag will not be part of a
    single line block.
    """
    last_index = 0
    inline = tuple(config.ignored_blocks_inline_IMSX.finditer(item))

    if inline:
        last_index = (
            inline[-1].end()
        )  # get the last index. The ignored opening should start after this.

    return bool(config.ignored_block_opening_IX.search(item[last_index:]))


def is_script_style_block_opening(config: Config, item: str) -> bool:
    """Find ignored group opening.

    A valid ignored group opening tag will not be part of a
    single line block.
    """
    last_index = 0
    inline = tuple(config.script_style_inline_IMSX.finditer(item))

    if inline:
        last_index = (
            inline[-1].end()
        )  # get the last index. The ignored opening should start after this.

    return bool(config.script_style_opening_IX.search(item[last_index:]))


def inside_protected_trans_block(
    config: Config, html: str, match: re.Match[str]
) -> bool:
    """Find ignored group closing.

    A valid ignored group closing tag will not be part of a
    single line block.

    True = non indentable > inside ignored trans block
    False = indentable > either inside a trans trimmed block, or somewhere else, but not a trans non trimmed :)
    """
    last_index = 0
    close_block = config.ignored_trans_blocks_closing_IX.search(match.group())

    if not close_block:
        return False

    non_trimmed = tuple(
        re.finditer(config.ignored_trans_blocks, html, flags=RE_FLAGS_ISX)
    )

    trimmed = tuple(
        re.finditer(config.trans_trimmed_blocks, html, flags=RE_FLAGS_ISX)
    )

    # who is max?
    if non_trimmed and (
        not trimmed or non_trimmed[-1].end() > trimmed[-1].end()
    ):
        # non trimmed!
        # check that this is not an inline block.
        non_trimmed_inline = any(
            re.finditer(
                config.ignored_trans_blocks, match.group(), flags=RE_FLAGS_ISX
            )
        )

        if non_trimmed_inline:
            last_index = non_trimmed[
                -1
            ].end()  # get the last index. The ignored opening should start after this.

            return bool(
                re.search(
                    config.ignored_trans_blocks_closing,
                    html[last_index:],
                    flags=RE_FLAGS_IX,
                )
            )

        return close_block.end(0) <= non_trimmed[-1].end()

    if trimmed:
        # inside a trimmed block, we can return true to continue as if
        # this is a indentable block
        return close_block.end(0) > trimmed[-1].end()
    return False

    # print(close_block)
    # if non_trimmed:
    #     last_index = (
    #         non_trimmed[-1].end()
    #     )  # get the last index. The ignored opening should start after this.

    # return re.search(
    #     config.ignored_trans_blocks_closing,
    #     html[last_index:],
    #     flags=RE_FLAGS_IX,
    # )


def is_ignored_block_closing(config: Config, item: str) -> bool:
    """Find ignored group closing.

    A valid ignored group closing tag will not be part of a
    single line block.
    """
    last_index = 0
    inline = tuple(config.ignored_inline_blocks_IX.finditer(item))

    if inline:
        last_index = (
            inline[-1].end()
        )  # get the last index. The ignored opening should start after this.

    return bool(config.ignored_block_closing_IX.search(item[last_index:]))


def is_script_style_block_closing(config: Config, item: str) -> bool:
    """Find ignored group closing.

    A valid ignored group closing tag will not be part of a
    single line block.
    """
    last_index = 0
    inline = tuple(config.script_style_inline_IX.finditer(item))

    if inline:
        last_index = (
            inline[-1].end()
        )  # get the last index. The ignored opening should start after this.

    return bool(
        re.search(
            config.script_style_closing, item[last_index:], flags=RE_FLAGS_IX
        )
    )


def is_safe_closing_tag(config: Config, item: str) -> bool:
    """Find ignored group opening.

    A valid ignored group opening tag will not be part of a
    single line block.
    """
    last_index = 0
    inline = tuple(config.ignored_group_opening_IMSX.finditer(item))

    if inline:
        last_index = (
            inline[-1].end()
        )  # get the last index. The ignored opening should start after this.

    return bool(config.safe_closing_tag_IX.search(item[last_index:]))


def inside_template_block(
    config: Config, html: str, match: re.Match[str]
) -> bool:
    """Check if a re.Match is inside of a template block."""
    match_start = match.start()
    match_end = match.end(0)
    for ignored_match in config.template_blocks_IMSX.finditer(html):
        if (
            ignored_match.start(0) <= match_start
            and match_end <= ignored_match.end()
        ):
            return True
    return False


def inside_ignored_linter_block(
    config: Config, html: str, match: re.Match[str]
) -> bool:
    """Check if a re.Match is inside of a ignored linter block."""
    match_start = match.start()
    match_end = match.end(0)
    for ignored_match in re.finditer(
        config.ignored_linter_blocks, html, flags=RE_FLAGS_IMSX
    ):
        if (
            ignored_match.start(0) <= match_start
            and match_end <= ignored_match.end()
        ):
            return True
    return False


@cache
def _inside_ignored_block(
    html: str,
    /,
    *,
    ignored_blocks: re.Pattern[str],
    ignored_inline_blocks: re.Pattern[str],
) -> tuple[tuple[int, int], ...]:
    return tuple(
        (x.start(0), x.end())
        for x in itertools.chain(
            ignored_blocks.finditer(html), ignored_inline_blocks.finditer(html)
        )
    )


def inside_ignored_block(
    config: Config, html: str, match: re.Match[str]
) -> bool:
    """Do not add whitespace if the tag is in a non indent block."""
    match_start = match.start()
    match_end = match.end(0)
    for ignored_match_start, ignored_match_end in _inside_ignored_block(
        html,
        ignored_blocks=config.ignored_blocks_IMSX,
        ignored_inline_blocks=config.ignored_inline_blocks_IX,
    ):
        if (
            ignored_match_start <= match_start
            and match_end <= ignored_match_end
        ):
            return True
    return False


@cache
def _child_of_unformatted_block(
    html: str, /, *, unformatted_blocks: re.Pattern[str]
) -> tuple[tuple[int, int], ...]:
    return tuple(
        (x.start(0), x.end()) for x in unformatted_blocks.finditer(html)
    )


def child_of_unformatted_block(
    config: Config, html: str, match: re.Match[str]
) -> bool:
    """Do not add whitespace if the tag is in a non indent block."""
    match_start = match.start()
    match_end = match.end(0)
    for ignored_match_start, ignored_match_end in _child_of_unformatted_block(
        html, unformatted_blocks=config.unformatted_blocks_IMSX
    ):
        if ignored_match_start < match_start and match_end <= ignored_match_end:
            return True
    return False


def child_of_ignored_block(
    config: Config, html: str, match: re.Match[str]
) -> bool:
    """Do not add whitespace if the tag is in a non indent block."""
    match_start = match.start()
    match_end = match.end(0)
    for ignored_match in itertools.chain(
        re.finditer(config.ignored_blocks, html, flags=RE_FLAGS_IMSX),
        config.ignored_inline_blocks_IX.finditer(html),
    ):
        if (
            ignored_match.start(0) < match_start
            and match_end <= ignored_match.end()
        ):
            return True
    return False


def overlaps_ignored_block(
    config: Config, html: str, match: re.Match[str]
) -> bool:
    """Do not add whitespace if the tag is in a non indent block."""
    match_start = match.start()
    match_end = match.end()

    for ignored_match in itertools.chain(
        re.finditer(config.ignored_blocks, html, flags=RE_FLAGS_IMSX),
        config.ignored_inline_blocks_IX.finditer(html),
    ):
        # don't require the match to be fully inside the ignored block.
        # poorly build html will probably span ignored blocks and should be ignored.
        if (ignored_match.start(0) <= match_start <= ignored_match.end()) or (
            ignored_match.start() <= match_end <= ignored_match.end()
        ):
            return True
    return False


def inside_ignored_rule(
    config: Config, html: str, match: re.Match[str], rule: str
) -> bool:
    """Check if match is inside an ignored pattern."""
    match_start = match.start()
    match_end = match.end()

    for rule_regex in config.ignored_rules:
        for ignored_match in re.finditer(rule_regex, html, flags=RE_FLAGS_ISX):
            if (
                rule in re.split(r"\s|,", ignored_match.group(1).strip())
                and (
                    ignored_match.start(0) <= match_start <= ignored_match.end()
                )
            ) or (
                not ignored_match.group(1).strip()
                and (ignored_match.start(0) <= match_end <= ignored_match.end())
            ):
                return True
    return False
