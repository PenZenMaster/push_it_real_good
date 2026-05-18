# Push It Real Good - Project Status

Last Updated: 2026-05-17

## Completed

- [x] Core WordPress REST API publishing logic (`post_pusher.py`)
- [x] PyQt6 GUI front-end (`push_it_ui_mvp.py`)
- [x] Drag-and-drop image widget (`image_drop_widget.py`)
- [x] Basic .gitignore (credentials excluded)
- [x] Project scaffolding: CLAUDE.md, pyproject.toml, requirements-dev.txt
- [x] Pre-commit hook configuration (.pre-commit-config.yaml)
- [x] TDD test scaffold (tests/test_post_pusher.py)

## Completed

- [x] Install dev dependencies into venv (all 38 packages, Python 3.13.12)
- [x] Fix requirements.txt encoding (UTF-16 LE -> UTF-8)
- [x] Fix test_publish_file_moves_file_after_post (12/12 tests passing)

## In Progress

- [ ] pre-commit hooks installed in venv (run install on next session start)

## Deferred / Backlog

- [ ] Move credentials from config.json to .env / environment variables
- [ ] Add tests for push_it_ui_mvp.py (GUI logic isolation)
- [ ] Add integration test against a local WP test instance
- [ ] CI/CD pipeline (GitHub Actions)

## Next Session Priorities

1. Run `venv\Scripts\pre-commit install --hook-type pre-commit --hook-type pre-push`
2. Pick up next feature or bug fix from backlog
