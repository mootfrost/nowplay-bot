{
  description = "python+uv";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        commonLibs = [
          pkgs.pkg-config
          pkgs.openssl
          pkgs.zlib
          pkgs.sqlite
          pkgs.libffi
          pkgs.readline
          pkgs.postgresql.pg_config
          pkgs.python313Packages.greenlet
        ];

        mkPythonShell = python: pkgs.mkShell {
          buildInputs = [ pkgs.uv python ] ++ commonLibs;
          shellHook = ''
            echo "uv + ${python.pname} ${python.version} ready"
          '';
        };

      in {
        devShells = {
          default = mkPythonShell pkgs.python313;
          py312 = mkPythonShell pkgs.python312;
          py313 = mkPythonShell pkgs.python313;
        };
      });
}
