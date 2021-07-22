#!/bin/sh

exec $(nix-build "$(dirname "$0")" --no-out-link)/bin/enter-env.sh "$@"
