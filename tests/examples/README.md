# Test Examples

*sasoptpy* includes several examples for users and test purposes.
To keep examples clean and easy to follow, there are a few steps when adding a new example.

## Contributing

### 1. Adding the Python example

Place your example under one of the subfolders: client_side, server_side or notebooks

- `client_side` folder is intended for problems where data is on the client-side.
- `server-side` folder is intended for problems where data is on the server-side.
- `notebooks` includes Jupyter notebooks and blog posts.

Follow remaining steps when adding a client-side or server-side example.
Such problems must have the following structure:
```
import sasoptpy as so
...

def test(cas_conn):

    m = so.Model(name='{myproblem}', session=cas_conn)
    ...
    m.solve()
    ...
    return m.get_objective_value()
```

### 2. Adding problem to the documentation

Create a markdown file under `/doc/examples` folder.
Name should be in the form of `{myproblem}.rst` and should include three parts

- Reference: Reference to where problem is taken from
- Model: A literal include of the python file added in step 1
- Output: A suppressed python import and a call of the problem with session

See existing problems under `/doc/examples` for quick reference.

### 3. Adding problem to unit tests

There are three different unit tests we have for each example:
- Final objective value (with SAS Viya)
- Final objective value (with SAS 9.4)
- Generated `OPTMODEL` code

1. Modify `/tests/examples/test_examples.py` by adding a new method in the following format:  
    ```
    def test_{myproblem}(self):
      from {myproblem} import test
      obj = self.run_test(test)
      self.assertAlmostEqual(obj, {expected_obj_value}, self.digits)
    ```

2. Add same method to `/tests/examples/test_examples_local.py`

3. Add generated (expected) `OPTMODEL` code under `/tests/examples/responses` folder as a `.sas` file.  
  Add a reference to this file inside `/tests/examples/responses.py` file in the following format:  
    ```
    {myproblem} = [
     read_file('problem_0'),
     read_file('problem_1'),
    ]
    ```  
    Finally add a generator test inside `/tests/examples/test_generators.py` in the following format:
    ```
    def test_{myproblem}(self):
       self.set_expectation('My Problem', expected.{myproblem})
       from {myproblem} import test
       test(TestGenerators.server)
       self.check_results()
    ```
