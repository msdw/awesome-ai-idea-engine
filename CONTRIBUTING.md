# Contributing to Awesome AI Idea Engine

Thank you for your interest in contributing. This repository is community-driven but maintainer-validated — all submissions are reviewed before merging.

## Ways to Contribute

### Suggest a new idea

Open an issue using the [Suggest Idea template](https://github.com/msdw/awesome-ai-idea-engine/issues/new?template=suggest-idea.yml).

Your submission should include:
- A specific target user (not "anyone")
- A real pain point or workflow problem
- A clear description of the AI role in the solution
- At least one business model hypothesis
- At least one validation step
- An honest difficulty estimate

### Suggest a resource

Open an issue using the [Suggest Resource template](https://github.com/msdw/awesome-ai-idea-engine/issues/new?template=suggest-resource.yml).

### Report a problem

If you find broken links, hype language, outdated information, or quality issues: open a [Problem Report](https://github.com/msdw/awesome-ai-idea-engine/issues/new?template=report-problem.yml).

## Quality Bar

### What gets accepted

- Specific, actionable ideas connected to real users and workflows
- Ideas with honest difficulty estimates (no "takes 2 hours to build")
- Ideas that acknowledge risks and compliance requirements
- Ideas backed by observable signals (job boards, Reddit, forums, industry reports)

### What gets rejected

- Ideas using language like: "guaranteed income", "passive income", "easy money", "make $10k", "no effort", "automatic revenue", "risk-free", "secret method"
- Spam automation or deceptive outreach ideas
- Ideas in regulated domains (health, finance, legal) without compliance notes
- Ideas that are too vague to evaluate ("build an AI assistant for businesses")
- Duplicate submissions

## Pull Request Guidelines

If you're submitting a PR directly:

1. Follow the YAML schema in `data/ideas.yaml` exactly
2. Run `python scripts/validate_yaml.py` locally before submitting
3. Run `python scripts/validate_marketing_language.py` to check for forbidden phrases
4. Fill in the PR checklist completely

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
