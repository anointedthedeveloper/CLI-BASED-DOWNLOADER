{pkgs}: {
  deps = [
    pkgs.tk
    pkgs.xorg.libxcb
    pkgs.xorg.libXft
    pkgs.xorg.libXrender
    pkgs.xorg.libXext
    pkgs.xorg.libX11
    pkgs.python312Packages.tkinter
  ];
}
