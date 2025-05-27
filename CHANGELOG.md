# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2025-05-27

### Changed

- Pin `certbot` dependency to 4.0.0

### Removed

- Remove support for Python 3.8

## [0.3.0] - 2024-10-25

### Changed

- Upgrade images to Python 3.11
- Change `$IMAGE_REPOSITORY`

### Removed

- Remove support for Python 3.7

## [0.2.1] - 2024-07-23

### Changed

- Rebuild docker image with newer dependencies: certbot 2.11.0, requests 2.32.3

## [0.2.0] - 2023-11-16

### Fixed

- Properly handle the creation of a certificate for a wildcard domain and the corresponding base domain simultaneously.

## [0.1.2] - 2023-11-15

### Fixed

- Fix wildcard example in documentation

### Changed

- Rebuild docker image with newer dependencies: certbot 2.7.4, requests 2.31.0

## [0.1.1] - 2023-03-06

### Added

- Publish official Docker image

## [0.1.0] - 2022-12-01

### Added

- Initial Release
