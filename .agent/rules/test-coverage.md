---
trigger: always_on
---

The goal of this rule is to generate the right level of test coverage and must be started when you are asked to reach this level.
All commands below must be in a virtual environment started with `source ./.venv/bin/activate`.
The current test coverage results are stored in the file named .coverage. This is a binary file and you get its content in a readable way using the command `coverage report --sort=cover --skip-covered -m --fail-under=80 --omit='scripts/*,manage.py,cousinsmatter/asgi.py,cousinsmatter/wsgi.py,*/views_test.py,*/migrations/*,cousinsmatter/htmlvalidator.py'.

In this file, some sources are not covered at 80% by existing tests (see Cover column) and the lines and line ranges in the "Missing" column are those which are not covered. Make sure the test coverage is 80% for all these files. The way to test coverage is to run `make cover t=<testname> o='--data-file=<testname>.cov.txt` and read the result in <testname>.cov.txt. Don't make too much effort to go beyond 80% of coverage and no effort at all to go above 85%.