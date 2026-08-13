# AGENTS.md
 
## Setup commands
- Setup venv: `uv sync`
- Run tests: `uv run python -m unittest`

## Testing instructions
- Prefer unit tests over integration tests with mocking of external dependencies
- Prefer integration tests over end-to-end tests with mocking of external dependencies
- Testable structure is preferred over coverage, i.e. code should be structured in a way that allows for easy testing of individual components without requiring the entire system to be running.
- Some functionality can only be tested with end-to-end tests, but these should be kept to a minimum and only used when necessary.