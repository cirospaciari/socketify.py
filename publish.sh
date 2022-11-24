python3 ./setup.py bdist_wheel --plat-name=any
pypy3 ./setup.py bdist_wheel --plat-name=any
python3 -m build -s
python3 -m twine upload -r testpypi dist/* --verbose
python3 -m pip install socketify --extra-index-url https://test.pypi.org/simple/