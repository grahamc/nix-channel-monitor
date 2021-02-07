let
  pkgs = import (builtins.fetchTarball "channel:nixos-unstable-small") {};
in
pkgs.resholvePackage {
  pname = "nix-channel-monitor";
  version = "0.0.0";

  src = ./src;
  preBuild = ''
    shellcheck ./calculate
  '';
  nativeBuildInputs = [ pkgs.shellcheck ];
  installPhase = ''
    install -Dv calculate $out/bin/calculate
  '';

  solutions.calculate = {
    scripts = [ "bin/calculate" ];
    interpreter = "${pkgs.oil}/bin/osh";

    inputs = with pkgs; [
      coreutils
      curl
      findutils
      gawk
      git
      gnugrep
      gnused
      telnet
    ];
  };
}
/*


    set - eux
    remote=https://github.com/nixos/nixpkgs.git
  if [ ! -d /var/lib/nix-channel-monitor/git ];
  then
  git clone "$remote" git
  fi
  git -C /var/lib/nix-channel-monitor/git remote set-url origin "$remote"



  ${src} /var/lib/nix-channel-monitor/git ${config.services.nginx.virtualHosts."channels.nix.gsc.io".root}
*/
