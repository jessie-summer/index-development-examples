# Index Development - Illustrative Code Samples

Independently written Python examples of common workflows in equity index development: data QC, sample selection, weighting, and evaluation. Built for learning and portfolio purposes; all schemas and parameters are synthetic and illustrative.

## Files (in reading order)

1. `1_inspect_data.py` - data QC: full vs key-level duplicates, full vs partial missing values
2. `2_index_selection.py` - three selection approaches: direct top-n, multi-factor scoring, industry-loop selection
3. `3_index_weighting.py` - pool-split weighting, per-stock caps, segment total cap, industry-neutral weighting, weight factors
4. `4_index_evaluation.py` - NAV backtest, performance stats, turnover, capacity, days-to-build, weight distributions

## Assumptions

1. Input data is a long panel keyed by (date, ticker); the backtest takes a wide price table (date x ticker).
2. Expected columns are generic: close (adjusted or total-return prices), free_float_mcap, industry, layer (core/noncore), plus factor fields where needed.
3. Factor fields are oriented so that higher is better; names missing a required factor are excluded from scoring.
4. Caps, thresholds and pool splits are illustrative parameters; the weighting functions validate feasibility and raise instead of returning weights that break their constraints.
5. The backtest requires held names to exist in the price table with complete prices, and raises otherwise. Distributions and corporate actions are assumed to be reflected in adjusted / total-return prices; transaction costs are not modeled.

## Disclaimer

1. This is a personal demonstration project using synthetic schemas and illustrative parameters; it is not production-ready code.
2. It does not include employer or client data, production code, proprietary methodology rules, or confidential documentation, and it is not intended to reproduce any specific organization's methodology or production process.
3. It does not represent the views or products of any organization and does not constitute investment advice; the code is provided as is, without warranty of any kind.

## Requirements

Python 3.9+, pandas, numpy.
