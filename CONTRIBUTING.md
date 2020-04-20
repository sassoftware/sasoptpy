# Contributing to sasoptpy

We welcome all contributions including bug reports, new features,
documentation fixes, performance enchancements, and new ideas.

## Submitting a Pull Request

If you have a contribution to make, submit a pull request using GitHub.
You need to add a unit test for any source code changes, including bug fixes.
Except for minor fixes, pull requests that do not have a unit test will not be accepted.
If your change drops the code coverage, you may be asked to write additional
unit tests.

You must include the text from the ContributerAgreement.txt file
along with your sign-off verifying that the change originated from you.

## Testing

Python [unittest](https://docs.python.org/3/library/unittest.html) are used for testing sasoptpy.

Automated testing is performed using GitLab for internal development,
but you can run unit tests in a Python environment.

In order to run all the tests, you need to have certain environment variables set:

* CAS Environment Variables:
  * __CASHOST__: Host or IP address for CAS sessions
  * __CASPORT__: Port number for CAS session
  * __AUTHINFO__: The location of your `.authinfo` file, that includes your username and password
  * __CASUSERNAME__: User name for the CAS session. This is required if `AUTHINFO` does not exist.
  * __CASPASSWORD__: Password for the CAS session. This is required if `AUTHINFO` does not exist.
* SAS Environment Variables:
  * __SASHOST__: Host or IP address for SAS installation
  * __SASPATH__: Absolute path of the SAS installation in the host

The CAS server should be active at runtime.

You can start running all the unit tests under `tests` folder as follows:

``` shell
python -m unittest discover -s tests/ -p 'test*.py'
```

If you install `coverage` package, you can see the total coverage of the unit tests.
Under `tests` you can run `test_coverage.sh` (or `test_coverage.bat`) to see the final coverage.
HTML pages will be created under `tests/html` folder.

## Documentation

The sasoptpy documentation is generated using [Sphinx](https://www.sphinx-doc.org/en/master/).
Documentation is generated in both HTML (for web view) and LaTeX (for PDF file) formats.

Sphinx handles both function APIs using the source files and Markdown files under `doc` folder.
Configuration for Sphinx can be found under `doc/conf.py` file.
A script is available for generating both formats `doc/makedocs.sh`.

Final sasoptpy documentation is generated using a script at

https://github.com/sertalpbilal/sasoptpy_doc_generator

You can generate the multi-version documentation pages using [`generate_latest.sh`](https://github.com/sertalpbilal/sasoptpy_doc_generator/blob/master/generate_latest.sh) script, found
in the repository.

A [docker image](https://hub.docker.com/r/sertalpbilal/sphinx_dev/dockerfile) is available at Docker Hub
that includes all dependencies.
