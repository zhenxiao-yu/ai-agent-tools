# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Repo-level `AGENTS.md` guidance for multi-agent contribution flows.
- Tag-based GitHub release workflow for curated GitHub Releases.

### Changed
- `.gitignore` updated for 2026 local AI tooling, editor state, and release hygiene.
- MIT license added for clearer open-source reuse terms.

## [1.1.0] - 2026-05-07

### Added
- Modular dashboard structure across config, data, services, pages, and UI modules.

### Fixed
- Dashboard paths now resolve from the repository root instead of requiring a fixed `C:\ai-agent-tools` location.
- Repository allowlist expanded beyond Node projects to support Python, Rust, Go, Java, Gradle, and generic versioned repos.

### Changed
- Dashboard help text now clarifies the supported repository types.
