{
  description = "leading-zeros-dates Python development environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-26.05-darwin";

  outputs = { nixpkgs, ... }:
    let
      systems = [ "aarch64-darwin" "x86_64-darwin" ];
    in {
      devShells = nixpkgs.lib.genAttrs systems (system:
        let pkgs = import nixpkgs { inherit system; };
        in {
          default = pkgs.mkShell {
            packages = [ pkgs.python312 pkgs.uv ];
            shellHook = ''
              export PROJECT_DEV_SHELL="leading-zeros-dates"
              export DEV_SHELL_PYTHON="${pkgs.python312}/bin/python3.12"
              export PYTHONNOUSERSITE=1
              unset PYTHONHOME
              export PYTHONPATH="${pkgs.python312Packages.tkinter}/${pkgs.python312.sitePackages}"
              export UV_PYTHON_DOWNLOADS=never
              export VIRTUAL_ENV="$PWD/.venv-nix"
              export PATH="$VIRTUAL_ENV/bin:$PATH"
              echo "leading-zeros-dates: run bash scripts/setup-dev.sh to sync dependencies."
            '';
          };
        });
    };
}
