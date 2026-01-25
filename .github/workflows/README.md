# CI/CD Workflows Documentation

This directory contains GitHub Actions workflows that automate testing, code quality checks, documentation building, and deployment for the Gas Swelling Model project.

## Overview

The CI/CD pipeline ensures code quality, catches issues early, validates documentation builds, and enables rapid iteration with confidence. All workflows run automatically on pushes and pull requests to main branches.

## Workflow Files

### 1. Tests Workflow (`test.yml`)

**Purpose:** Automated testing with pytest across multiple Python versions and operating systems.

**Triggers:**
- Push to `main`, `master`, or `develop` branches
- Pull requests to `main`, `master`, or `develop` branches
- Manual workflow dispatch

**Jobs:**

#### Test Matrix
- **Operating Systems:** Ubuntu, Windows, macOS
- **Python Versions:** 3.8, 3.9, 3.10, 3.11, 3.12
- **Total Combinations:** 15 test environments

#### Test Steps
1. Checkout code
2. Set up Python with pip caching
3. Install dependencies with `pip install -e .[dev]`
4. Run pytest with coverage:
   ```bash
   pytest tests/ -v --tb=short --cov=gas_swelling --cov-report=term-missing --cov-report=xml
   ```
5. Upload coverage to Codecov (Ubuntu 3.11 only)

#### Minimal Dependencies Test
- Runs on Ubuntu with Python 3.11
- Installs only core dependencies: `numpy`, `scipy`, `pytest`
- Ensures package works without optional dev dependencies

#### Basic Lint Check
- Runs critical flake8 checks for syntax errors (E9, F63, F7, F82)
- Runs style checks with `--exit-zero` (doesn't fail the build)
- **Note:** Comprehensive linting is handled by `lint.yml`

**Badge:**
```markdown
![Tests](https://github.com/Etoile04/gas-swelling-model/workflows/Tests/badge.svg)
```

---

### 2. Linting Workflow (`lint.yml`)

**Purpose:** Comprehensive code quality enforcement using flake8 and related plugins.

**Triggers:**
- Push to `main`, `master`, or `develop` branches
- Pull requests to `main`, `master`, or `develop` branches
- Manual workflow dispatch

**Jobs:**

#### 1. Lint Flake8 (Critical Errors)
- **Checks:** Python syntax errors (E9), undefined names (F63, F7, F82)
- **Action:** Fails the build on critical errors
- **Command:**
  ```bash
  flake8 gas_swelling/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
  ```

#### 2. Lint Flake8 (Style Checks)
- **Checks:** Code style, complexity, line length
- **Configuration:**
  - Max complexity: 10
  - Max line length: 127 characters
- **Action:** Reports style issues and fails the build
- **Command:**
  ```bash
  flake8 gas_swelling/ tests/ --count --max-complexity=10 --max-line-length=127 --statistics
  ```

#### 3. Lint Imports
- **Plugin:** `flake8-import-order`
- **Checks:** Import statement ordering and style
- **Ignores:** I100, I101, I102 (specific import ordering rules)
- **Command:**
  ```bash
  flake8 gas_swelling/ tests/ --select=I --extend-ignore=I100,I101,I102
  ```

#### 4. Lint Docstrings
- **Plugin:** `flake8-docstrings`
- **Checks:** Docstring presence and style (PEP 257)
- **Ignores:** D100, D104, D105, D107 (module, package, nested, init docstrings)
- **Command:**
  ```bash
  flake8 gas_swelling/ --select=D --extend-ignore=D100,D104,D105,D107
  ```

#### 5. Type Hint Check (Optional)
- **Tool:** mypy (if available)
- **Action:** Continues on error (doesn't fail the build)
- **Purpose:** Optional static type checking for better code quality

**Installed Linters:**
- `flake8` - Core linting engine
- `flake8-docstrings` - Docstring style checking
- `flake8-bugbear` - Additional error detection
- `flake8-import-order` - Import organization checking

**Badge:**
```markdown
![Lint](https://github.com/Etoile04/gas-swelling-model/workflows/Lint/badge.svg)
```

---

### 3. Documentation Build Workflow (`docs.yml`)

**Purpose:** Build Sphinx documentation to verify it compiles correctly.

**Triggers:**
- Push to `main`, `master`, or `develop` branches
- Pull requests to `main`, `master`, or `develop` branches
- Manual workflow dispatch

**Jobs:**

#### Build Docs
- **OS:** Ubuntu latest
- **Python:** 3.11

**Steps:**
1. Checkout code
2. Set up Python 3.11 with pip caching
3. Install dependencies:
   ```bash
   pip install -e .
   pip install -r docs/requirements.txt
   ```
4. Build HTML documentation:
   ```bash
   cd docs
   make html
   ```
5. Upload documentation artifacts:
   - **Name:** `documentation-html`
   - **Path:** `docs/_build/html/`
   - **Retention:** 30 days

**Notes:**
- The workflow includes commented-out deployment steps
- Actual deployment is handled by `pages-deploy.yml`

**Badge:**
```markdown
![Docs](https://github.com/Etoile04/gas-swelling-model/workflows/Docs/badge.svg)
```

---

### 4. Pages Deploy Workflow (`pages-deploy.yml`)

**Purpose:** Automatically deploy documentation to GitHub Pages.

**Triggers:**
- Push to `main` or `master` branches (production deployments)
- Manual workflow dispatch

**Permissions:**
```yaml
permissions:
  contents: write
```

**Jobs:**

#### Deploy
- **OS:** Ubuntu latest
- **Python:** 3.11

**Steps:**
1. Checkout code
2. Set up Python 3.11 with pip caching
3. Install dependencies:
   ```bash
   pip install -e .
   pip install -r docs/requirements.txt
   ```
4. Build HTML documentation:
   ```bash
   cd docs
   make html
   ```
5. Deploy to GitHub Pages using `peaceiris/actions-gh-pages@v3`:
   - **Token:** Automatic `GITHUB_TOKEN`
   - **Publish directory:** `./docs/_build/html`

**Result:**
Documentation is automatically published to: `https://etoile04.github.io/gas-swelling-model/`

**Badge:**
```markdown
![Pages](https://github.com/Etoile04/gas-swelling-model/workflows/Pages/badge.svg)
```

---

## Status Badges

All workflows include status badges displayed at the top of `README.md`:

| Badge | Description | Workflow File |
|-------|-------------|---------------|
| ![Tests](https://github.com/Etoile04/gas-swelling-model/workflows/Tests/badge.svg) | Test status across all Python versions and OSes | `test.yml` |
| ![codecov](https://codecov.io/gh/Etoile04/gas-swelling-model/branch/main/graph/badge.svg) | Code coverage percentage | `test.yml` (via Codecov) |
| ![Lint](https://github.com/Etoile04/gas-swelling-model/workflows/Lint/badge.svg) | Code quality and linting status | `lint.yml` |
| ![Docs](https://github.com/Etoile04/gas-swelling-model/workflows/Docs/badge.svg) | Documentation build status | `docs.yml` |
| ![Pages](https://github.com/Etoile04/gas-swelling-model/workflows/Pages/badge.svg) | GitHub Pages deployment status | `pages-deploy.yml` |

## Workflow Dependencies

```
test.yml (independent)
  └─> Coverage upload to Codecov

lint.yml (independent)
  ├─> Critical error checks
  ├─> Style checks
  ├─> Import order checks
  ├─> Docstring checks
  └─> Type hint checks (optional)

docs.yml (independent)
  └─> Upload artifacts (30-day retention)

pages-deploy.yml (depends on docs.yml conceptually)
  └─> Deploy to GitHub Pages on main/master
```

## CI/CD Pipeline Flow

### On Push to Feature Branch
1. **Tests** run on all OS/Python combinations
2. **Linting** checks code quality
3. **Docs** build validates documentation
4. Results appear in PR checks

### On Push to Main/Master
1. All above checks run
2. **Pages Deploy** builds and publishes documentation to GitHub Pages
3. Badges update automatically
4. Coverage data uploaded to Codecov

### On Pull Request
1. All checks run (except pages deployment)
2. Reviewers see test/lint/docs status
3. Must pass checks before merge (if branch protection enabled)

## Local Testing Before Push

### Run Tests Locally
```bash
# Install dependencies
pip install -e .[dev]

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=gas_swelling --cov-report=term-missing
```

### Run Linting Locally
```bash
# Install linters
pip install flake8 flake8-docstrings flake8-bugbear flake8-import-order

# Run all checks
flake8 gas_swelling/ tests/ --count --max-complexity=10 --max-line-length=127

# Critical checks only
flake8 gas_swelling/ tests/ --select=E9,F63,F7,F82 --show-source
```

### Build Documentation Locally
```bash
# Install dependencies
pip install -e .
pip install -r docs/requirements.txt

# Build docs
cd docs
make html

# View output
open _build/html/index.html  # macOS
xdg-open _build/html/index.html  # Linux
```

## Workflow Configuration

### Python Versions
- **Minimum supported:** 3.8
- **Primary testing:** 3.11
- **Latest tested:** 3.12

### Operating Systems
- **Primary:** Ubuntu (latest)
- **Secondary:** Windows, macOS (for test workflow only)

### Dependency Caching
All workflows use pip caching to speed up builds:
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: ${{ matrix.python-version }}
    cache: 'pip'
```

## Customization

### Adding New Python Version
Edit the matrix in `.github/workflows/test.yml`:
```yaml
matrix:
  python-version: ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"]  # Add 3.13
```

### Changing Linting Rules
Edit the flake8 commands in `.github/workflows/lint.yml`:
```bash
# Example: Increase max line length
flake8 gas_swelling/ tests/ --max-line-length=150
```

### Adding New Documentation
1. Update docs in `docs/` directory
2. Push to main branch
3. `pages-deploy.yml` automatically builds and publishes

### Excluding Files from Linting
Create `.flake8` configuration file:
```ini
[flake8]
exclude =
    .git,
    __pycache__,
    build,
    dist,
    *.egg-info
max-line-length = 127
```

## Troubleshooting

### Tests Fail but Pass Locally
- Check Python version mismatch
- Verify all dependencies installed: `pip install -e .[dev]`
- Check for environment-specific issues (OS differences)

### Linting Fails
- Run linters locally to see full output
- Fix critical errors first (E9, F63, F7, F82)
- Address style issues (complexity, line length)
- Add docstrings to public functions/classes

### Documentation Build Fails
- Build locally first: `cd docs && make html`
- Check for syntax errors in RST files
- Verify all imports work in documentation environment
- Check `docs/requirements.txt` for missing dependencies

### Pages Deploy Fails
- Verify repository has GitHub Pages enabled
- Check that `main` branch is set as Pages source
- Ensure build permissions are correct:
  ```yaml
  permissions:
    contents: write
  ```

## CI/CD Best Practices

1. **Always run tests locally** before pushing
2. **Keep PRs focused** to make review easier
3. **Fix linting issues** as they appear
4. **Update documentation** when changing code
5. **Check workflow status** before merging PRs
6. **Monitor coverage** and aim for high coverage
7. **Use workflow artifacts** to debug failed builds

## Related Documentation

- [Project README](../../README.md) - Main project documentation
- [INSTALL.md](../../INSTALL.md) - Installation guide
- [CLAUDE.md](../../CLAUDE.md) - Developer guidelines
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Support

For CI/CD issues:
1. Check workflow logs in the Actions tab
2. Review this documentation
3. Open an issue with the workflow name and error message
