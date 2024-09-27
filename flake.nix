{
  description = "A basic flake with a shell";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake_utils.url = "github:numtide/flake-utils";
    poetry2nix.url = "github:nix-community/poetry2nix";
  };

  outputs = { nixpkgs, flake_utils, poetry2nix, ... }:
    flake_utils.lib.eachDefaultSystem (system:
      let
        # Common variables
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ poetry2nix.overlays.default ];
        };

        # Dependencies
        git_deps = with pkgs; [ git openssl cacert ];
        dev_deps = with pkgs; [
          (poetry.override { python3 = python312; })
          bashInteractive
          gnumake
          nixfmt
          nodePackages.prettier
        ];
        all_deps = dev_deps ++ git_deps;

        # Overrides
        poetry_overrides = pkgs.poetry2nix.defaultPoetryOverrides.extend
          (final: prev: {
            decli = prev.decli.overridePythonAttrs (old: {
              buildInputs = (old.buildInputs or [ ]) ++ [ prev.poetry ];
            });
            pyright = prev.pyright.overridePythonAttrs (old: {
              buildInputs = (old.buildInputs or [ ]) ++ [ prev.setuptools ];
            });
          });

        # Releaser derivation
        releaserApp = pkgs.poetry2nix.mkPoetryApplication {
          projectDir = ./.;
          python = pkgs.python312;
          checkGroups = [ ];
          overrides = poetry_overrides;
        };
        releaserEnv = pkgs.poetry2nix.mkPoetryEnv {
          projectDir = ./.;
          python = pkgs.python312;
          editablePackageSources = { releaser = ./src; };
          overrides = poetry_overrides;
        };

        # Wrapped releaser application
        wrappedReleaserApp = pkgs.writeShellApplication {
          name = "releaser-app";
          runtimeInputs = [ releaserApp ] ++ git_deps;
          text = ''
            ${releaserApp}/bin/releaser "$@"
          '';
        };

      in {
        devShells.default =
          releaserEnv.env.overrideAttrs (oldAttrs: { buildInputs = all_deps; });
        apps.default = {
          type = "app";
          program = "${wrappedReleaserApp}/bin/releaser-app";
        };
      });
}
