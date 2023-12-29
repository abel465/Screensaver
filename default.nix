{
  pkgs,
  python,
  ...
}:
pkgs.stdenv.mkDerivation {
  name = "screensaver";

  src = ./.;

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  installPhase = ''
    mkdir -p $out/bin
    cp screensaver.py $out
    echo "${python}/bin/python $out/screensaver.py \$@" > $out/bin/screensaver
    chmod +x $out/bin/screensaver
    wrapProgram $out/bin/screensaver --prefix PATH : ${pkgs.lib.makeBinPath [pkgs.ghostscript_headless]}
  '';
}
