"""Create the same explicitly synthetic measurements in the live builder's input format."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f'refusing to replace {args.output}')
    with Path(__file__).with_name('synthetic_observations.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row['readout'] = float(row['readout'])
        row['gene_target'] = row['target']
        row['dataset_kind'] = 'synthetic_smoke_fixture'
        row['note'] = ('Invented arithmetic fixture, not biological observations. '
                       'Compute group means only; no significance or mechanistic inference.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), args.output)
    print(args.output)


if __name__ == '__main__':
    main()
