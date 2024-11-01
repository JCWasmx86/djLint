"""Collection of shared djLint functions."""
# ruff: noqa: ERA001

from __future__ import annotations

import hashlib
import itertools
from typing import TYPE_CHECKING

import regex as re

if TYPE_CHECKING:
    from .settings import Config

child_of_unformatted_block_cache_: dict[str, list[tuple[int, int]]] = {}
inside_ignored_block_cache_: dict[str, list[tuple[int, int]]] = {}
RE_FLAGS_VI = re.VERBOSE | re.IGNORECASE
RE_FLAGS_IV = RE_FLAGS_VI
RE_FLAGS_IMVD = re.IGNORECASE | re.MULTILINE | re.VERBOSE | re.DOTALL
RE_FLAGS_IVM = re.IGNORECASE | re.VERBOSE | re.MULTILINE
RE_FLAGS_IMV = re.IGNORECASE | re.MULTILINE | re.VERBOSE
RE_FLAGS_IVD = re.IGNORECASE | re.VERBOSE | re.DOTALL


def child_of_unformatted_block_cache(
    config: Config, html: str
) -> list[tuple[int, int]]:
    key = hashlib.sha256(
        (html + config.unformatted_blocks).encode("utf-8")
    ).hexdigest()
    if key in child_of_unformatted_block_cache_:
        return child_of_unformatted_block_cache_[key]
    matches = [
        (x.start(0), x.end())
        for x in re.finditer(
            config.unformatted_blocks,
            html,
            flags=RE_FLAGS_IMVD,
        )
    ]
    child_of_unformatted_block_cache_[key] = matches
    return matches


def inside_ignored_block_cache(
    config: Config, html: str
) -> list[tuple[int, int]]:
    key = hashlib.sha256(
        (html + config.unformatted_blocks).encode("utf-8")
    ).hexdigest()
    if key in inside_ignored_block_cache_:
        return inside_ignored_block_cache_[key]
    matches = [
        (x.start(0), x.end())
        for x in itertools.chain(
            re.finditer(
                config.ignored_blocks,
                html,
                flags=RE_FLAGS_IMVD,
            ),
            re.finditer(
                config.ignored_inline_blocks,
                html,
                flags=RE_FLAGS_IV,
            ),
        )
    ]
    inside_ignored_block_cache_[key] = matches
    return matches


def is_ignored_block_opening(config: Config, item: str) -> bool:
    """Find ignored group opening.

    A valid ignored group opening tag will not be part of a
    single line block.
    """
    last_index = 0
    inline = tuple(
        re.finditer(
            config.ignored_blocks_inline,
            item,
            flags=RE_FLAGS_IMVD,
        )
    )

    if inline:
        last_index = (
            inline[-1].end()
        )  # get the last index. The ignored opening should start after this.

    return bool(
        re.search(
            config.ignored_block_opening,
            item[last_index:],
            flags=RE_FLAGS_IV,
        )
    )


def is_script_style_block_opening(config: Config, item: str) -> bool:
    """Find ignored group opening.

    A valid ignored group opening tag will not be part of a
    single line block.
    """
    last_index = 0
    inline = tuple(
        re.finditer(
            config.script_style_inline,
            item,
            flags=RE_FLAGS_IMVD,
        )
    )

    if inline:
        last_index = (
            inline[-1].end()
        )  # get the last index. The ignored opening should start after this.

    return bool(
        re.search(
            config.script_style_opening,
            item[last_index:],
            flags=RE_FLAGS_IV,
        )
    )


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
    close_block = re.search(
        config.ignored_trans_blocks_closing,
        match.group(),
        flags=RE_FLAGS_IV,
    )

    if not close_block:
        return False

    non_trimmed = tuple(
        re.finditer(
            config.ignored_trans_blocks,
            html,
            flags=RE_FLAGS_IVD,
        )
    )

    trimmed = tuple(
        re.finditer(
            config.trans_trimmed_blocks,
            html,
            flags=RE_FLAGS_IVD,
        )
    )

    # who is max?
    if non_trimmed and (
        not trimmed or non_trimmed[-1].end() > trimmed[-1].end()
    ):
        # non trimmed!
        # check that this is not an inline block.
        non_trimmed_inline = any(
            re.finditer(
                config.ignored_trans_blocks,
                match.group(),
                flags=RE_FLAGS_IVD,
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
                    flags=RE_FLAGS_IV,
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
    #     flags=RE_FLAGS_IV,
    # )


def is_ignored_block_closing(config: Config, item: str) -> bool:
    """Find ignored group closing.

    A valid ignored group closing tag will not be part of a
    single line block.
    """
    last_index = 0
    inline = tuple(
        re.finditer(
            config.ignored_inline_blocks, item, flags=RE_FLAGS_IV
        )
    )

    if inline:
        last_index = (
            inline[-1].end()
        )  # get the last index. The ignored opening should start after this.

    return bool(
        re.search(
            config.ignored_block_closing,
            item[last_index:],
            flags=RE_FLAGS_IV,
        )
    )


def is_script_style_block_closing(config: Config, item: str) -> bool:
    """Find ignored group closing.

    A valid ignored group closing tag will not be part of a
    single line block.
    """
    last_index = 0
    inline = tuple(
        re.finditer(
            config.script_style_inline, item, flags=RE_FLAGS_IV
        )
    )

    if inline:
        last_index = (
            inline[-1].end()
        )  # get the last index. The ignored opening should start after this.

    return bool(
        re.search(
            config.script_style_closing,
            item[last_index:],
            flags=RE_FLAGS_IV,
        )
    )


def is_safe_closing_tag(config: Config, item: str) -> bool:
    """Find ignored group opening.

    A valid ignored group opening tag will not be part of a
    single line block.
    """
    last_index = 0
    inline = tuple(
        re.finditer(
            config.ignored_inline_blocks + r" | " + config.ignored_blocks,
            item,
            flags=RE_FLAGS_IMVD,
        )
    )

    if inline:
        last_index = (
            inline[-1].end()
        )  # get the last index. The ignored opening should start after this.

    return bool(
        re.search(
            config.safe_closing_tag,
            item[last_index:],
            flags=RE_FLAGS_IV,
        )
    )


def inside_template_block(
    config: Config, html: str, match: re.Match[str]
) -> bool:
    """Check if a re.Match is inside of a template block."""
    return any(
        ignored_match.start(0) <= match.start()
        and match.end(0) <= ignored_match.end()
        for ignored_match in re.finditer(
            config.template_blocks,
            html,
            flags=RE_FLAGS_IMVD,
        )
    )


def inside_ignored_linter_block(
    config: Config, html: str, match: re.Match[str]
) -> bool:
    """Check if a re.Match is inside of a ignored linter block."""
    return any(
        ignored_match.start(0) <= match.start()
        and match.end(0) <= ignored_match.end()
        for ignored_match in re.finditer(
            config.ignored_linter_blocks,
            html,
            flags=RE_FLAGS_IMVD,
        )
    )


def inside_ignored_block(
    config: Config, html: str, match: re.Match[str]
) -> bool:
    """Do not add whitespace if the tag is in a non indent block."""
    match_start = match.start()
    match_end = match.end(0)
    return any(
        ignored_match[0] <= match_start and match_end <= ignored_match[1]
        for ignored_match in inside_ignored_block_cache(config, html)
    )


def child_of_unformatted_block(
    config: Config, html: str, match: re.Match[str]
) -> bool:
    """Do not add whitespace if the tag is in a non indent block."""
    match_start = match.start()
    match_end = match.end(0)
    ignored_matches = child_of_unformatted_block_cache(config, html)
    if ignored_matches == []:
        return False
    for ignored_match in ignored_matches:
        if ignored_match[0] < match_start and match_end <= ignored_match[1]:
            return True
    return False


def child_of_ignored_block(
    config: Config, html: str, match: re.Match[str]
) -> bool:
    """Do not add whitespace if the tag is in a non indent block."""
    return any(
        ignored_match.start(0) < match.start()
        and match.end(0) <= ignored_match.end()
        for ignored_match in itertools.chain(
            re.finditer(
                config.ignored_blocks,
                html,
                flags=RE_FLAGS_IMVD,
            ),
            re.finditer(
                config.ignored_inline_blocks,
                html,
                flags=RE_FLAGS_IV,
            ),
        )
    )


def overlaps_ignored_block(
    config: Config, html: str, match: re.Match[str]
) -> bool:
    """Do not add whitespace if the tag is in a non indent block."""
    return any(
        # don't require the match to be fully inside the ignored block.
        # poorly build html will probably span ignored blocks and should be ignored.
        (
            ignored_match.start(0) <= match.start()
            and match.start() <= ignored_match.end()
        )
        or (
            ignored_match.start(0) <= match.end()
            and match.end() <= ignored_match.end()
        )
        for ignored_match in itertools.chain(
            re.finditer(
                config.ignored_blocks,
                html,
                flags=re.DOTALL
                | re.IGNORECASE
                | re.VERBOSE
                | re.MULTILINE
                | re.DOTALL,
            ),
            re.finditer(
                config.ignored_inline_blocks,
                html,
                flags=RE_FLAGS_IV,
            ),
        )
    )


def inside_ignored_rule(
    config: Config, html: str, match: re.Match[str], rule: str
) -> bool:
    """Check if match is inside an ignored pattern."""
    for rule_regex in config.ignored_rules:
        for ignored_match in re.finditer(
            rule_regex, html, flags=RE_FLAGS_IVD
        ):
            if (
                rule in re.split(r"\s|,", ignored_match.group(1).strip())
                and (
                    ignored_match.start(0) <= match.start()
                    and match.start() <= ignored_match.end()
                )
            ) or (
                not ignored_match.group(1).strip()
                and (
                    ignored_match.start(0) <= match.end()
                    and match.end() <= ignored_match.end()
                )
            ):
                return True
    return False
