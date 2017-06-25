```
usage: gitScrabber [-t file] [-r file] [-o file] [-c file] [-d dir] [-p] [-f]
                   [-h] [--github-token str]

ScrabGitRepos

Required arguments:
  -t file, --tasks file
                        Path to the tasks.yaml file - can be provided via
                        configuration file

Program arguments:
  -r file, --report file
                        Path to an old report as base
  -o file, --output file
                        Path where the report will be saved to
  -c file, --config file
                        Path to the configuration file - defaults to
                        './gitScrabber.conf'. Write the command line arguments
                        without leading dashes e.g.:
                        print
                        data=/tmp
  -d dir, --data dir    Directory where the repositories and archives are
                        stored
  -p, --print           If the report should be printed to stdout - defaults
                        to false
  -f, --force           Forces the override of a present report - defaults to
                        false
  -h, --help            Show this help message and exit

Global arguments:
  --github-token str    Access token for github to work with a higher query
                        limit against their api
```

Dependencies:

- If not already installed:
    - `python3-pip`
    - `python3-setuptools`
- `packaging`
- `pyunpack`
- `ruamel.yaml`

