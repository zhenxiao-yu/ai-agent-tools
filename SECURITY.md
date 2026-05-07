# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| Latest on `master` | Yes |
| Older tagged releases | Best effort |

## Reporting a Vulnerability

Please do **not** open a public GitHub issue for security vulnerabilities.

Report vulnerabilities privately by email to **markyu0615@gmail.com** with:
- a description of the issue and potential impact
- reproduction steps or proof of concept
- any suggested mitigation if you have one

You should receive an acknowledgement within 72 hours for a valid report.

## Scope

This repository mainly contains local automation, dashboard utilities, prompts, and workflow docs. The highest-risk areas are:
- accidental secret exposure in scripts or docs
- unsafe automation that modifies git state or local files unexpectedly
- command injection or untrusted input handling in automation scripts
- local dashboard features that expose sensitive machine or repo data

## Disclosure Guidance

Please give reasonable time for investigation and remediation before public disclosure. If a report is confirmed, the fix will be documented in the changelog and release notes when appropriate.
