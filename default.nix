let
  # Temporarily pin Nixpkgs: https://github.com/NixOS/nixpkgs/pull/126993#issuecomment-884192962
  pkgs = import (builtins.fetchTarball "https://github.com/NixOS/nixpkgs/archive/578dd8d634f0a4666f7481f6ea9e578114da74f8.tar.gz") { };

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
