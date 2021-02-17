let
  pkgs = import (builtins.fetchTarball "channel:nixos-unstable-small") {};

  perl = pkgs.perl.withPackages (ps: with ps; [ JSON DateTime HTMLTidy ]);
in
pkgs.resholvePackage {
  pname = "nix-channel-monitor";
  version = "0.0.0";

  src = ./src;

  preBuild = ''
    shellcheck ./calculate
    shellcheck ./calculate-and-push
    shellcheck ./make-index
  '';

  buildPhase = ''
    patchShebangs .
  '';

  nativeBuildInputs = [ pkgs.shellcheck perl ];

  installPhase = ''
    install -Dv calculate $out/bin/calculate
    install -Dv calculate-and-push $out/bin/calculate-and-push
    install -Dv make-index $out/bin/make-index
  '';

  solutions.calculate = {
    scripts = [ "bin/calculate" "bin/calculate-and-push" ];
    interpreter = "${pkgs.oil}/bin/osh";

    inputs = with pkgs; [
      (placeholder "out")
      awscli2
      coreutils
      curl
      findutils
      gawk
      git
      gnugrep
      gnused
      jq
      recode
    ];
  };
}
