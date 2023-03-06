# certbot-dns-norisnetwork

noris network DNS Authenticator plugin for Certbot

An authenticator plugin for [certbot](https://certbot.eff.org/) to support ACMEv2 dns-01 challenge for domains the DNS zones of which are managed by noris network AG.

This plugin automates the process of completing a `dns-01` challenge by creating and subsequently removing TXT records using the [noris network ServiceAPI](https://service-api.noris.net/v1/docs/).


## Installation

Install the plugin:

* Via pip:
  ```
  pip install certbot-dns-norisnetwork
  ```
* From source:
  ```
  python3 setup.py install
  ```

## Preparation

The usage of this plugin requires a configuration file containing noris network `ServiceAPI Token` obtained from our [Customer Portal](https://service.noris.net/).


### Get your API Token

In case you don't have a noris API Token, you can acquire one by following the instructions found in our OpenAPI Docs:
- [Authentication mechanism for noris ServiceAPI](https://service-api.noris.net/v1/docs/#section/Introduction/Authentication)
- [Required Roles for your User](https://service-api.noris.net/v1/docs/#section/Introduction/Role-model)

Create you `noris API Token` and store it in a safe place.


### Configure your Login Details

Create a **credentials.ini** file and add the following content:
```
dns_noris_token=<norisAPIToken>
```

> Note: You should protect these API credentials as you would a password. Users who can read this file can use these credentials to issue arbitrary API calls on your behalf. Users who can cause Certbot to run using these credentials can complete a `dns-01` challenge to acquire new certificates or revoke existing certificates for associated domains, even if those domains aren't being managed by this server.

**Important Notes**

1. Make sure that the file is only readable by the user.

   Certbot will emit a warning if it detects that the `credentials.ini` file can be accessed by other users on your system. The warning includes "Unsafe permissions on credentials configuration file", followed by the path to the credentials file. This warning will be emitted each time Certbot uses the credentials file,including for renewal, and cannot be silenced except by addressing the issue.

    To restrict access to the file:
    ```sh
    chmod 600 /path/to/credentials.ini
    ```


2. The path to the `credentials.ini` file can be provided interactively or using the `--dns-noris-credentials` command-line argument. Certbot records the path to this file for use during renewal, but does not store the file's contents.

### Ensure access to Certbot

Apart from the `credentials.ini` file, Certbot user should have write access to the `logs`, `work` and `config` directories as well.

You can use the following options to overwrite the default locations, if needed:
* `--logs-dir` option to overwrite the default location (`/var/log/letsencrypt/`) for logs
* `--work-dir` option to overwrite the default location (`/var/log/letsencrypt/`) for working directory
* `--config-dir` option to overwrite the default location (`/etc/letsencrypt/`) for config directory.
    * This is where the acquired certificate will be added.


## Usage

> **WARNING**: Non-ASCII domains provided through the `-d` argument should be in punycode format (`xn--`)!

1. Acquire a certificates for `example.com`:

    ```sh
    certbot certonly \
        -a dns-noris \
        --dns-noris-credentials /path/to/credentials.ini \
        --non-interactive \
        --agree-tos \
        -m 'my.email@mail.com' \
        -d example.com
    ```

2. Acquire a certificate for both `example.com` and `www.example.com`:
    ```sh
    certbot certonly \
        -a dns-noris \
        --dns-noris-credentials /path/to/credentials.ini \
        --non-interactive \
        --agree-tos \
        -m 'my.email@mail.com' \
        -d example.com \
        -d www.example.com
    ```

3. Acquire a certificate for `example.com` waiting 240 seconds for DNS propagation from the command line:
    ```sh
    certbot certonly \
        -a dns-noris \
        --dns-noris-credentials /path/to/credentials.ini \
        --dns-noris-propagation-seconds 240 \
        --non-interactive \
        --agree-tos \
        -m 'my.email@mail.com' \
        -d example.com
    ```


## Command Line Options
---------------

Available command-line options originating from `dns-noris` Authenticator:
```
--dns-noris-credentials DNS_NORIS_CREDENTIALS
    Path to credentials INI file.
        Default: /etc/letsencrypt/credentials.ini

--dns-noris-propagation-seconds DNS_NORIS_PROPAGATION_SECONDS
    The number of seconds to wait for DNS to propagate before asking the ACME server to verify the DNS record.
        Default: 60
```
For all the available command-line options originating from `Certbot` you can use [Certbot's documentation](https://eff-certbot.readthedocs.io/en/stable/using.html#certbot-command-line-options).


## Docker

In order to create a docker container with a `certbot-dns-norisnetwork` installation,  you can use our **official Docker image**:

```sh
docker pull norisnetwork/certbot-dns-norisnetwork
```

> Note: **Before running the app**, make sure that the path to credentials (set by `--dns-noris-credentials` arg) reside in a volume-mounted directory (e.g. in `/etc/letsencrypt/`).

The application can be run as follows::
```sh
docker run --rm \
    -v /var/lib/letsencrypt:/var/lib/letsencrypt \
    -v /etc/letsencrypt:/etc/letsencrypt \
    norisnetwork/certbot-dns-norisnetwork certonly \
    --authenticator dns-noris \
    --dns-noris-propagation-seconds 60 \
    --dns-noris-credentials /etc/letsencrypt/credentials.ini \
    --agree-tos \
    --keep-until-expiring --non-interactive \
    --server https://acme-v02.api.letsencrypt.org/directory \
    -m 'user@mail.com'
    -d example.com -d '*.example.com'
```


## Developer Guide

### Tools

Use `pip` to install all the required dev tools:

```sh
pip install -e .[dev]
```

#### Code Formatter

Use **Black** Python code formatter:

```sh
black certbot_dns_norisnetwork/
black tests/
black setup.py
```

#### Code Analyzer

Use **pylint** for static code analyzing:

```sh
pylint certbot_dns_norisnetwork/
pytlint tests/
```

#### Type Annotations Checker

Use **mypy** for type checking:

```sh
mypy certbot_dns_norisnetwork/
mypy tests/
```

### New Release

Use **bump2version** for release versioning.

Run the following commands to trigger a new release:

```sh
bump2version patch # possible: major | minor | patch
git push <remote-repo> && git push <remote-repo> --tags
```

This will adjust the version appropriately and create a tagged commit that will act as a trigger for the build and publish GitLab pipelines.
