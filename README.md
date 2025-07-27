# GraphQL Authorization Checker

This repository contains a small utility script that inspects GraphQL type
definitions to find fields that return certain types without specifying
an `authorize:` rule. It is intended to help locate potentially
unauthorized exposures in a larger Ruby on Rails code base.

## Files

- `check_auth.py` &ndash; Python script that performs the analysis.
- `noauthtypes.txt` &ndash; list of GraphQL type files that do not define
  their own authorization.
- `types_ce/` and `types_ee/` &ndash; directories that should contain the
  GraphQL type files (Ruby files) to scan.

## Usage

Ensure that the `types_ce` and `types_ee` directories contain the
GraphQL type definitions referenced in `noauthtypes.txt`. Run the script
with Python 3:

```bash
python3 check_auth.py
```

The script prints a JSON object describing any occurrences where a field
returns a type from `noauthtypes.txt` but does not include an
`authorize:` argument. Each entry lists the file containing the missing
authorization along with the field name and location.

The tool relies on the `grep` command being available in your
environment.
