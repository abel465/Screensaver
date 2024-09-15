{
  description = "Screensaver";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = {
    self,
    flake-utils,
    nixpkgs,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs {inherit system;};

      python = pkgs.python3Packages.python.withPackages (ps:
        with ps; [
          tkinter
          pillow
          cairosvg
          pyheif
          python-vlc
        ]);
    in {
      devShell = with pkgs;
        mkShell {
          buildInputs = [
            python
            ghostscript_headless
            swayidle
          ];
        };

      packages.default = pkgs.callPackage ./default.nix {inherit python;};
      apps.${system}.default = "${pkgs.default}/bin/screensaver";
    });
}
