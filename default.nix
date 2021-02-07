let
  pkgs = import (builtins.fetchTarball "channel:nixos-unstable-small") {};
in
pkgs.resholvePackage {
  pname = "nix-channel-monitor";
  version = "0.0.0";

  src = ./src;
  preBuild = ''
    shellcheck ./calculate
    shellcheck ./calculate-and-push
  '';
  nativeBuildInputs = [ pkgs.shellcheck ];
  installPhase = ''
    install -Dv calculate $out/bin/calculate
    install -Dv calculate-and-push $out/bin/calculate-and-push
  '';

  solutions.calculate = {
    scripts = [ "bin/calculate" "bin/calculate-and-push" ];
    interpreter = "${pkgs.oil}/bin/osh";

    inputs = with pkgs; [
      (placeholder "out")
      coreutils
      curl
      findutils
      gawk
      git
      gnugrep
      gnused
      jq
      telnet
    ];
  };
}
