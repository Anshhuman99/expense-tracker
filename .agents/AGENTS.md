# Custom Agent Configuration Rules
- **Flat File Structure**: Custom agents must be defined as flat `.md` files placed directly inside the `.agents/agents/` directory (e.g., `.agents/agents/spendly-test-runner.md`).
- **Do Not Nest**: Do not create subdirectories for custom agents (e.g., `.agents/agents/spendly-test-runner/spendly-test-runner.md` is invalid) and do not use `agent.json` formats.
- **YAML Frontmatter**: The `.md` file must begin with a YAML frontmatter block specifying metadata (like `name`, `description`, and `tools`).
