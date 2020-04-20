# Unit Tests

*sasoptpy* uses Python Unit Tests to ensure each commit brings a non-breaking change.

Unit tests are classified based on which component it is related to.
Our main aim is to add unit tests along with every code change to increase or keep the code coverage the same.

## Running unit tests

All unit tests can be run using 

``` bash
python -m unittest discover -s tests/ -p 'test*.py'
```

This would run all the python files under `/tests` folder starting with `test`.

## Code coverage

Code coverage is tested using `coverage` package. Use `test_coverage.sh` file to run the script.

Running `test_coverage.sh` generates `html` folder, which can be displayed using a browser.

### Single test coverage

Each individual test file aims to provide highest level of code coverage.
If you need to run a single test to check code coverage, run `test_single.sh` script with following arguments:

```bash
./test_single.sh {path_to_specific_test.py}
```

This will update the code coverage folder under `html`.

