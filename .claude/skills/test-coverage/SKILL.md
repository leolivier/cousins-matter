---
name: test coverage
description: run test coverage at the right level
---

# Test coverage
* The goal of this rule is to generate the right level of test coverage
* make sure the coverage package defined in pyproject.toml is installed before starting
* All commands below must be run in a virtual environment started with `source ./.venv/bin/activate`.
* To compute the current coverage, run `make cover` or `make cover [to=<test options>] [co=<coverage options>] [a=<application>]`
* If the `[a=<application>]`is used the binary result of the test coverage is stored in .coverage.$(a) otherwise in .coverage.
* The coverage file is a binary file. To read its content, use the command `coverage report --sort=cover --skip-covered -m --fail-under=80 --omit='core/tasks_schedules.py,scripts/*,config/*,core/settings.py,manage.py,cousinsmatter/asgi.py,cousinsmatter/wsgi.py,core/htmlvalidator.py,*/views_test.py,*/migrations/*,*/tests/*,scripts/*,config/*,core/settings.py,manage.py,cousinsmatter/asgi.py,cousinsmatter/wsgi.py,*/views_test.py,*/migrations/*,core/htmlvalidator.py'--data-file=<coverage file>
* In this report, some sources are not covered at 80% by existing tests (see Cover column) and the lines and line ranges in the "Missing" column are those which are not covered. Make sure the test coverage is 80% for all these files.
* The way to test coverage is to run `make cover t=<testname> o='--data-file=<testname>.cov.txt` and read the result in <testname>.cov.txt.
* Don't make too much effort to generate tests and go beyond 80% of coverage and no effort at all to go above 85%. If coverage is less than 80% for one file and non covered code is managing corner cases hard to reproduce, ask the user if you must generate a test to cover them.
