{
  description = "Screensaver";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs {inherit system;};

      python = pkgs.python311Packages.python.withPackages (ps:
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
          ];
        };
    });
}
