# Contributing to browser-use

We love contributions! Please read through these links to get started:

 - 🔢 [Contribution Guidelines](https://docs.browser-use.com/development/contribution-guide)
 - 👾 [Local Development Setup Guide](https://docs.browser-use.com/development/local-setup)
 - 🏷️ [Issues Tagged: `#help-wanted`](https://github.com/browser-use/browser-use/issues?q=is%3Aissue%20state%3Aopen%20label%3A%22help%20wanted%22)

For development, select Node 26 from `.node-version` before running Pyright
or the pre-commit hooks (`nvm install "$(cat .node-version)" && nvm use "$(cat .node-version)"` if you use nvm). On Linux,
Node.js 26 also requires `libatomic` (`sudo apt install libatomic1` on Debian/Ubuntu).
The Python package does not require a system Node.js installation; optional
external MCP servers have their own runtime requirements.
