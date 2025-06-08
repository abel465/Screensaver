{
  description = "Screensaver";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
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
          pillow-heif
          python-vlc
        ]);
    in rec {
      devShell = with pkgs;
        mkShell {
          buildInputs = [
            python
            swayidle
          ];
        };
      packages.default = pkgs.stdenv.mkDerivation {
        name = "screensaver";
        src = ./.;
        nativeBuildInputs = [
          pkgs.makeWrapper
        ];
        installPhase = ''
          mkdir -p $out/bin
          cp screensaver.py \
            screensaver_raw.py \
            screensaver_from_config.py \
            screensaver_options_gui.py \
            options.py \
            screensaver.service \
            $out
          echo "${python}/bin/python $out/screensaver.py \$@" > $out/bin/screensaver
          chmod +x $out/bin/screensaver
          wrapProgram $out/bin/screensaver --prefix PATH : ${with pkgs;
            lib.makeBinPath [
              swayidle
            ]}
        '';
      };
      apps.default = {
        type = "app";
        program = "${packages.default}/bin/screensaver";
      };
    });
}
