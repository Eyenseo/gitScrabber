```
usage: gitScrabber [-h] -t file [-g dir] [-r file] [-s file] [-p] [-f]

ScrabGitRepos

optional arguments:
  -h, --help            show this help message and exit
  -t file, --tasks file
                        Path to the tasks.yaml file
  -g dir, --gitdir dir  Directory where the repositories are cloned to
  -r file, --report file
                        Path to an old report as base.
  -s file, --savereport file
                        Path where the report will be saved to.
  -p, --printreport     If the report should be printed to stdout
  -f, --force           Forces the override of a present report
```
