# Contributing to TFKit

We’re excited that you’re interested in contributing to **TFKit – Terraform Intelligence & Analysis Suite**!  
TFKit is built by and for infrastructure engineers who value clean code, clarity, and automation.  
Your ideas, feedback, and contributions make the project better for everyone.

---

## 🧭 How to Contribute

There are several ways to contribute:

- 🐛 **Report Bugs** – Use GitHub Issues with a clear title and reproduction steps.
- 💡 **Suggest Features** – Propose new features or enhancements via feature requests.
- 🧪 **Improve Tests** – Add or enhance test coverage to ensure stability.
- 📘 **Improve Documentation** – Help make the documentation clearer or more complete.
- 🧩 **Contribute Code** – Add new capabilities or fix issues in the core modules.

---

## ⚙️ Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/ivasik-k7/tfkit.git
cd tfkit
```

### 2. Create a Virtual Environment

```bash
uv venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
uv sync
```

### 4. Run Tests

```bash
uv run pytest tests/ -v
```

---

## 🧱 Code Guidelines

- Follow **PEP 8** for Python code style.
- Use **type hints** wherever possible.
- Keep functions modular, focused, and well-documented.
- Prefer **Click** for CLI argument handling and **Rich** for terminal output.
- Include **docstrings** for all public functions and classes.
- Use **logging** or TFKit’s internal log mechanisms for all operational output.

---

## ✅ Pull Request Process

1. Fork the repository.
2. Create a feature branch:

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. Make your changes with clear, descriptive commits.
4. Ensure tests pass:

   ```bash
   pytest
   ```

5. Lint your code (we use `flake8`):

   ```bash
   flake8 tfkit/
   ```

6. Update documentation as needed.
7. Submit your pull request with a clear description and link to any related issue.

---

## 🧪 Testing Standards

All new functionality must include tests. We use:

- **pytest** for unit testing
- **coverage.py** for test coverage reporting

To run tests and measure coverage:

```bash
pytest --cov=tfkit tests/
```

---

## 🧭 Commit Message Convention

We follow a simplified version of **Conventional Commits**:

| Type        | Description                                           |
| ----------- | ----------------------------------------------------- |
| `feat:`     | A new feature                                         |
| `fix:`      | A bug fix                                             |
| `docs:`     | Documentation-only changes                            |
| `test:`     | Adding or correcting tests                            |
| `refactor:` | Code changes that neither fix a bug nor add a feature |
| `chore:`    | Maintenance or tooling updates                        |

Example:

```
feat(scan): add provider summary section in scan results
```

---

## 🧑‍💻 Code of Conduct

Please note that this project is governed by a [Code of Conduct](./CODE_OF_CONDUCT.md).
By participating, you agree to uphold its principles.

---

## 🙌 Acknowledgment

Thank you for helping make TFKit better! Every contribution, no matter how small, helps move the Terraform community forward.
