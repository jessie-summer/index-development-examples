# Index Construction - Illustrative Code Samples

## Purpose

1. This repository is a set of independently written, illustrative code samples covering the common functions behind a rules-based equity index: data QC, sample selection, weighting, and pre-launch evaluation.
2. It is built for learning and portfolio purposes, to show how I structure this kind of logic in my own coding practice.
3. All logic shown is transparent and generic: standard, publicly known techniques commonly used in index selection, weighting and evaluation.
4. It does not contain or refer to any specific project, client case, or undisclosed information, and it is not intended to reproduce any real index production process.
5. These are demonstration samples, not production-ready code: there is no exhaustive input validation, and the backtest assumes dividends, corporate actions and trading costs are already reflected in the price series.

## Files

1. `functions/1_inspect_data.py` - data QC: full vs key-level duplicates, full vs partial missing values
2. `functions/2_index_selection.py` - three selection approaches: direct top-n, multi-factor scoring, industry-loop selection
3. `functions/3_index_weighting.py` - pool-split weighting, per-stock caps, segment total cap, industry-neutral weighting, weight factors
4. `functions/4_index_evaluation.py` - NAV backtest, performance stats, turnover, capacity, days-to-build, weight distributions
5. `example.py` - minimal end-to-end demo on a synthetic snapshot: selection -> weighting -> evaluation

## Assumptions

1. Input data is a long panel keyed by (date, ticker); the backtest takes a wide price table (date x ticker).
2. Expected columns are generic: close (adjusted or total-return prices), free_float_mcap, industry, layer (core/noncore), plus factor fields where needed.
3. Factor fields are oriented so that higher is better; names missing a required factor are excluded from scoring.
4. Caps, thresholds and pool splits are illustrative parameters; the weighting functions validate feasibility and raise instead of returning weights that break their constraints.
5. The backtest requires complete prices for held names and rebalance dates present in the price index, and raises otherwise.

## Disclaimer

1. This is a personal demonstration project created using synthetic schemas and illustrative parameters.
2. It does not include employer or client data, production code, proprietary methodology rules, or confidential documentation.
3. The examples implement general index-construction concepts and are not intended to reproduce any specific organization's methodology or production process.
4. This repository does not represent the views, products, or methodologies of any organization, and does not constitute investment advice.
5. The code is provided as is, for demonstration purposes only, without warranty of any kind.

## Run

```bash
python example.py
```

## Requirements

Python 3.9+, pandas, numpy.
