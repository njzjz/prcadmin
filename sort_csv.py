# SPDX-License-Identifier: LGPL-3.0-or-later
"""Sort output CSV file."""
# require Python 3.9 or later
import sys

if sys.version_info < (3, 9):
    raise RuntimeError("Python 3.9+ required.")

import argparse
import pandas

def sort_csv(input_fn, output_fn):
    """Sort output CSV file.

    Parameters
    ----------
    input_fn : str
        The input CSV file.
    output_fn : str
        The output CSV file.
    """
    df = pandas.read_csv(input_fn)
    df_sort = df.sort_values(by=["code"], ascending=True)
    df_sort.to_csv(output_fn, index=False)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Sort output CSV file.")
    parser.add_argument("input", help="The input CSV file.")
    parser.add_argument("output", help="The output CSV file.")
    args = parser.parse_args()
    sort_csv(args.input, args.output)

if __name__ == "__main__":
    main()