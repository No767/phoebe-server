# phoebe-server

The backend server for Phoebe, a platform for queer housing.

## About Phoebe

In light of safety amongst the LGBTQ+ community, many queer people face
difficulties and risk homelessness due to their identity. Acknowledging the
uphill battle, Phoebe was inspired to provide a platform where queer people can
search for safe alternatives provided by other queer folks.

Phoebe aims to match queer people with other queer folks who are struggling or
will struggle to find a place to live because of their queerness (e.g. being
transgender). It is often far more comfortable for queer people to live
together than living with those who may pose a risk. In addition, Phoebe also
accounts for polyamory relationships and offers the ability to seek housing in
groups.

You can see our [DevPost](https://devpost.com/software/phoebe-izav85) for more
information!

## Development

This project uses Nix for development. If you have Nix installed, you can simply
run `nix develop` to enter a development environment with all the necessary
dependencies.

Otherwise, you may use Poetry to set up your development environment.

Then, you can run the following commands:

```sh
./main.py --database :memory: --port 5469
```

## Testing

The backend comes with integration tests using `hurl`. You can run the tests
with the following command:

```sh
./tests/run
```

Note that `hurl` is installed in the Nix development environment, so you will
not need to install it separately.
