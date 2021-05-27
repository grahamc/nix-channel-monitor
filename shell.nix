{ pkgs ? import <nixpkgs> { } }:
pkgs.mkShell {
  propagatedBuildInputs = with pkgs; [
    awscli2
    black
    jq
    mypy
    pyright
    python3
    python3Packages.flake8
    python3Packages.isort
    python3Packages.requests
    vault
  ];
}
