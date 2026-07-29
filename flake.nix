{
  description = "plusfraisautravail - local Postgres + tools for the sites-conformes CMS";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs =
    { nixpkgs, ... }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in
    {
      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          # awscli2: used by `just sync-prod-media` (aws s3 sync against the
          # Scaleway S3-compatible endpoint).
          packages = [
            pkgs.postgresql_17
            pkgs.awscli2
          ];

          # PGDATA/PGHOST scoped to the repo, not ~/.local or a system
          # service - so `just db-*` never touches any other Postgres on
          # this machine, and deleting the repo cleans it up entirely.
          # PGHOST is a directory: Postgres listens on a Unix socket there
          # instead of a TCP port, so there's no port to collide with.
          shellHook = ''
            export PGDATA="$PWD/.pgdata"
            export PGHOST="$PWD/.pgrun"
            export PGDATABASE=cms
            export PGUSER=cms
            mkdir -p "$PGHOST"
          '';
        };
      });
    };
}
