{
	inputs = {
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
		}:

		flake-utils.lib.eachDefaultSystem (system:
			let
				pkgs = nixpkgs.legacyPackages.${system};
				inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; })
					mkPoetryApplication
					defaultPoetryOverrides;

			in
			{
				packages.default = mkPoetryApplication {
					projectDir = self;
					overrides = defaultPoetryOverrides.extend (self: super: let
						fixPoetryPackage = pkg: pkg.overridePythonAttrs (old: {
							buildInputs = (old.buildInputs or [ ]) ++ (with super; [
								setuptools
								poetry
							]);
						});
					in
						{
							sonyflake-py = fixPoetryPackage super.sonyflake-py;
							fastapi-pagination = fixPoetryPackage super.fastapi-pagination;
						}
					);
				};

				devShell = pkgs.mkShell {
					inputsFrom = [ self.packages.${system}.default ];

					packages = with pkgs; [
						poetry
						hurl
					];
				};
			}
		);
}
