Release checklist
=================
1. Run tests
2. Update version in setup.py
3. Update version in CHANGELOG
4. Run build CI
5. Create a git Release+tag (both title and tag are vA.B.C, description is CHANGELOG content)
6. Run `python3 setup.py sdist bdist_wheel` & `twine check dist/*`
7. Run `twine upload dist/*` (push the package to pypi)

CHANGELOG types of changes
==========================
`Added`      for new features.
`Changed`    for changes in existing functionality.
`Deprecated` for soon-to-be removed features.
`Removed`    for now removed features.
`Fixed`      for any bug fixes.
`Security`   for vulnerabilities.
