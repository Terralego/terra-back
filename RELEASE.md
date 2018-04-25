
# First time requirements: #
```
pip install twine
```
Create account on pypi and pypitest by going on websites.

Then create a ~/.pypirc file with:
```
[pypi]
repository: https://pypi.python.org/pypi
username: YOUR_USERNAME_HERE
password: YOUR_PASSWORD_HERE

[testpypi]
repository: https://test.pypi.org/legacy/
username: YOUR_USERNAME_HERE
password: YOUR_PASSWORD_HERE

```

# Checklist for releasing pypeman on pypi in version x.x.x #

- [ ] Update CHANGELOG.md
- [ ] Update version number (can also be minor or major)
```
vim terracommon/__init__.py 
```
- [ ] Install the package again for local development, but with the new version number:
```
python setup.py develop
```
- [ ] Run the tests and fix eventual errors:
```
tox
```
- [ ] Commit the changes:
```
git add CHANGELOG.md
git commit -m "Changelog for upcoming release x.x.x."
```
- [ ] tag the version
```
git tag x.x.x # The same as in terracommon/__init__py file
```
- [ ] push on git repository
```
git push --tags
```
- [ ] Generate packages:
```
python setup.py sdist bdist_wheel
```
- [ ] publish release on pypi and see result on https://testpypi.python.org/pypi :
```
twine upload -r testpypi dist/*
```
- [ ] Then when all is ok, release on PyPI by uploading both sdist and wheel:
```
twine upload dist/*
```

- [ ] Test that it pip installs:
```
mktmpenv
pip install my_project
<try out my_project>
deactivate
```

- [ ] Push: `git push`
- [ ] Push tags: `git push --tags`
- [ ] Check the PyPI listing page to make sure that the README, release notes, and roadmap display properly. If not, copy and paste the RestructuredText into http://rst.ninjs.org/ to find out what broke the formatting.

