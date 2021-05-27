#!/usr/bin/env python3

import contextlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Iterable

import requests

# Parse Arguments
GIT_REPO, DEST_STR = sys.argv[1:]

assert Path(GIT_REPO).is_dir()
DEST = Path(DEST_STR)
DEST.mkdir(exist_ok=True, parents=True)

# Environment Variables
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
REMOTE = os.environ.get("REMOTE", "origin")
SERVER = os.environ.get("SERVER")
URL = os.environ.get("URL", "https://channels.nix.gsc.io")


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


_indent = 0


def printi(*args, **kwargs):
    print("  " * _indent, end="")
    print(*args, **kwargs)


# Shell utils
def shell(command: str) -> str:
    command = command.strip()
    printi(f"+ {command}")
    ctx = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if ctx.returncode != 0:
        printi(f"  {bcolors.FAIL}ERROR:")
        output = (ctx.stderr.decode("utf-8") + ctx.stdout.decode("utf-8")).split("\n")
        for line in output:
            printi(f"  {line}")
        printi(f"  {bcolors.ENDC}")
        sys.exit(ctx.returncode)
    return ctx.stdout.decode("utf-8")


@contextlib.contextmanager
def pushd(directory: Path):
    global _indent
    old_dir = os.getcwd()
    os.chdir(directory)
    printi(f"+ pushd {directory}")
    _indent += 1
    try:
        yield
    finally:
        _indent -= 1
        printi("+ popd")
        os.chdir(old_dir)


def append_line_to_file(filename: Path, line: str):
    lines = []
    if filename.exists():
        with open(filename) as f:
            lines = f.readlines()

    # Add the new URL. Keep the last 100k URLs.
    lines.append(line)
    lines = lines[-100_000:]

    # Write the history back to history-url
    with open(filename, "w+") as f:
        f.writelines(lines)


# Matrix Utils
def matrix_request(
    endpoint: str,
    method: Callable,
    *args,
    **kwargs,
) -> requests.Response:
    if endpoint.startswith("/"):
        endpoint = endpoint[1:]
    endpoint = f"{SERVER}/_matrix/client/r0/{endpoint}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    return method(endpoint, headers=headers, *args, **kwargs)


def publish_update_to_matrix(branch: str, rooms: Iterable[str]):
    commit_sha = shell(f"git show -s --format='%h' {REMOTE}/{branch}").strip()
    commit_from = shell(f"git show -s --format='%cr' {REMOTE}/{branch}").strip()
    commit_url = f"https://github.com/NixOS/nixpkgs/commit/{commit_sha}"
    history_url = f"{URL}/{branch}/history"

    unformatted = (
        f"Channel {branch} advanced to {commit_url} "
        + f"(from {commit_from}, history: {history_url})"
    )
    formatted = f"""
        Channel {branch} advanced to <a href="{commit_url}">{commit_sha}</a>
        (from {commit_from}, <a href="{history_url}">history</a>)
    """

    # Publish the message to the room.
    data = {
        "msgtype": "m.notice",
        "body": unformatted,
        "format": "org.matrix.custom.html",
        "formatted_body": formatted,
    }

    printi(f"Change text: '{unformatted}'")

    # Send the message to the rooms.
    for room in rooms:
        printi(f"Publishing change to {room}")
        transaction_id = int(time.time())
        resp = matrix_request(
            f"rooms/{room}/send/m.room.message/{transaction_id}",
            method=requests.put,
            data=json.dumps(data),
        )

        assert resp.ok, (resp.reason, resp.text)


def main():
    global _indent
    # TODO figure out how to configure this.
    rooms = [
        "!wfRWMLdXruNtsaDaKU:sumnerevans.com",
    ]

    # Add the bot to the configured rooms.
    # If the account is already in the room, this is a no-op, so this is more efficient
    # than checking first and then adding.
    printi("Joining rooms:")
    for room in rooms:
        printi(f"  Joining {room}")
        matrix_request(f"join/{room}", method=requests.post)

    # Find all of the nixos-* nixpkgs-* branches.
    with pushd(GIT_REPO):
        shell(f"git fetch {REMOTE}")
        branches_output = shell(
            f"""
            git for-each-ref --format '%(refname:strip=3)' \
                "refs/remotes/{REMOTE}/nixos-*" "refs/remotes/{REMOTE}/nixpkgs-*"
            """
        )
        branches = map(
            lambda b: (b, b.replace("/", "_").replace("..", "_")),
            filter(
                lambda b: b != "" and "HEAD" not in b,
                branches_output.strip().split("\n"),
            ),
        )

    seconds_since_epoch = int(time.time())

    for branch, name in branches:
        # Make the directory to hold the branch metadata.
        branch_dir = Path(DEST) / name
        branch_dir.mkdir(exist_ok=True, parents=True)

        # Determine if the URL has changed.
        # ==============================================================================

        # Determine the channel URL.
        channel_request = requests.get(f"https://nixos.org/channels/{branch}")
        latest_url = channel_request.url

        # Get the previous URL from latest-url.
        latest_url_filename = branch_dir / "latest-url"
        prev_latest_url = None
        if latest_url_filename.exists():
            with open(latest_url_filename) as latest_url_file:
                prev_latest_url = latest_url_file.readline().split(" ")[0]

        # If the URL changed, update the latest-url and history-url file.
        if latest_url != prev_latest_url:
            printi(
                f"  {bcolors.BOLD}{bcolors.OKBLUE}Change in {branch} URL{bcolors.ENDC}"
            )

            latest_url_with_timestamp = f"{latest_url} {seconds_since_epoch}\n"

            # Update latest-url
            with open(latest_url_filename, "w+") as latest_url_file:
                latest_url_file.writelines(latest_url_with_timestamp)

            # Append the latest URL to the history-url file.
            history_url_filename = branch_dir / "history-url"
            append_line_to_file(history_url_filename, latest_url_with_timestamp)

        # Check if the commit has changed.
        # ==============================================================================
        latest_filename = branch_dir / "latest"
        prev_latest = None
        if latest_filename.exists():
            with open(latest_filename) as latest_file:
                prev_latest = latest_file.readline()

        # Calculate the new latest git commit.
        with pushd(GIT_REPO):
            latest = shell(f'git show -s --format="%H %at" "{REMOTE}/{branch}"')
        latest_v2 = f"{latest} {seconds_since_epoch}"

        if latest != prev_latest:
            printi(f"{bcolors.BOLD}{bcolors.OKBLUE}Change in {branch}{bcolors.ENDC}")
            with pushd(GIT_REPO):
                publish_update_to_matrix(branch, rooms)

            with open(latest_filename, "w+") as latest_file:
                latest_file.write(latest)

            # Append the latest line to the history file.
            history_filename = branch_dir / "history"
            append_line_to_file(history_filename, latest)

            # Note: latest-v2 doesn't do a hash check b/c
            # its hash always changes due to the date.
            latest_v2_filename = branch_dir / "latest-v2"
            with open(latest_v2_filename, "w+") as latest_v2_file:
                latest_v2_file.write(latest_v2)

            history_v2_filename = branch_dir / "history-v2"
            append_line_to_file(history_v2_filename, latest_v2)

        with open(branch_dir / "README.txt", "w+") as f:
            f.write(
                """This service is provided for free.

                If you use this service automatically, please be
                polite and follow som rules:

                  - please don't poll any more often than every 15
                    minutes to reduce the bandwidth costs.

                  - please consider using my webhooks instead:
                    email me at graham at grahamc dot com or
                    message @grahamc:nixos.org on #nix:nixos.org
                    on Matrix.

                FILE NOTES

                  Each format comes with two files, a "latest" file
                  and a "history" file.

                  The history files will retain 100000 lines of history.

                FORMAT NOTES

                  latest, history:
                    commit-hash date-of-commit

                  latest-v2, history-v2:
                    commit-hash date-of-commit date-of-advancement

                  latest-url, history-url:
                    channel-url date-of-advancement

                  Note: "date-of-advancement" is actually the date
                  the advancement was _detected_, and can be
                  wildly wrong for no longer updated channels. For
                  example, the nixos-13.10 channel's
                  date-of-advancement is quite recent despite the
                  channel not having updated in many years.

                  All three formats will continue to be updated.

                Thank you, good luck, have fun
                Graham
"""
            )


if __name__ == "__main__":
    main()
