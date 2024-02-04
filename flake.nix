{
	inputs = {
		flake-compat.url = "github:edolstra/flake-compat";
		flake-utils.url = "github:numtide/flake-utils";
		nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
		poetry2nix = {
			url = "github:nix-community/poetry2nix";
			inputs.nixpkgs.follows = "nixpkgs";
		};
	};

	outputs =
		{
			self,
			nixpkgs,
			poetry2nix,
			flake-utils,
			flake-compat,
		}:

		flake-utils.lib.eachDefaultSystem (system:
			let
				pkgs = nixpkgs.legacyPackages.${system};

				poetryApplication = mkPoetryApplication {
					projectDir = self;
					overrides = defaultPoetryOverrides.extend (self: super: let
						fixPoetryPackage = pkg: pkg.overridePythonAttrs (old: {
							buildInputs = (old.buildInputs or [ ]) ++ (with super; [
								setuptools
								poetry
								pdm-pep517
								pdm-backend
								truststore
							]);
						});
					in
						{
							broadcaster = fixPoetryPackage super.broadcaster;
							sonyflake-py = fixPoetryPackage super.sonyflake-py;
							sse-starlette = fixPoetryPackage super.sse-starlette;
							fastapi-pagination = fixPoetryPackage super.fastapi-pagination;
							sphinxcontrib-jquery = super.sphinxcontrib-jquery.overridePythonAttrs (old: {
								buildInputs = (old.buildInputs or [ ]) ++ (with super; [
									sphinx
								]);
							});
						}
					);
				};

				inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; })
					mkPoetryApplication
					defaultPoetryOverrides;
			in
			{
				packages = {
					default = poetryApplication.dependencyEnv;
				};
				devShell = pkgs.mkShell {
					inputsFrom = [ poetryApplication ];

					packages = with pkgs; [
						poetry
						hurl
					];
				};
			}
		);
}
