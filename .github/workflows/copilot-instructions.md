* IMPORTANT!!! Always use uv to run python commands and to manage dependencies. Example commands:
  * `uv add <package>`
  * `uv python3 -m <module>`
  * `uv run <script>.py`
  * `uv run pytest`
* Always validate that linting passes and that all tests pass after making changes
* **IMPORTANT!!!!** Assume both the frontend and backend are running on the 3080 for the frontend and 8180 for the backend with active reloading for changes. Only start if verified not running on the localhost.
