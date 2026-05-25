# Security Policy

## Reporting a Vulnerability

This repository contains documentation and Python scripts only. It does not operate a web service or process user data.

If you discover a security issue (e.g., a script that could be misused, a workflow with unsafe permissions), please open an issue with the label `security` or contact the maintainer directly.

## Scope

- Python scripts in `scripts/` — any command injection, path traversal, or unsafe subprocess usage
- GitHub Actions workflows — any overly permissive token scopes or injection risks
- No web service, no database, no user authentication to audit

## Response

We aim to respond to security reports within 5 business days.
