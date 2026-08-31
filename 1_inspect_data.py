# Demo of the common data QC situations before index calculation.
# Situation 1: fully duplicated rows -> count and drop
# Situation 2: key duplicates (same date+ticker, different values) -> flag and
#              explain first (extraction error / multi share class), fix by rule
# Situation 3: a column or one ticker fully missing -> upstream data issue
# Situation 4: partial missing -> judge against expectation (high missing rate
#              on revenue is a problem, missing dividends are normal)
import pandas as pd


def drop_full_duplicates(df):
    # identical on all columns, safe to drop
    n = df.duplicated().sum()
    print('fully duplicated rows:', n)
    return df.drop_duplicates()


def flag_key_duplicates(df, keys=('date', 'ticker')):
    # same key, different values: investigate before touching
    dup = df[df.duplicated(subset=list(keys), keep=False)]
    print('key-duplicated rows:', len(dup))
    if len(dup):
        print(dup.sort_values(list(keys)).head(10))
    return dup


def check_full_missing(df, field='close'):
    # whole column or one ticker's whole series missing -> upstream issue
    all_missing_cols = [c for c in df.columns if df[c].isna().all()]
    print('fully missing columns:', all_missing_cols if all_missing_cols else 'none')
    per_ticker = df.groupby('ticker')[field].apply(lambda s: s.isna().all())
    dead = list(per_ticker[per_ticker].index)
    print('tickers with %s fully missing:' % field, dead if dead else 'none')
    return dead


def missing_rates(df, expected_missing=('dividend',)):
    # partial missing: compare the rate against expectations for that field
    rates = df.isna().mean().round(4)
    print(rates)
    for c, r in rates.items():
        if r > 0 and c not in expected_missing:
            print('check field:', c, 'missing rate:', r)
    return rates


def fill_prices(df, limit=5):
    # gaps of up to `limit` days are filled in full; longer gaps are left
    # unfilled entirely (a partially filled suspension is a stale price) and dropped
    def fill_one(s):
        isna = s.isna()
        gap_id = (~isna).cumsum()
        gap_len = isna.groupby(gap_id).transform('sum')
        fillable = isna & (gap_len <= limit)
        return s.where(~fillable, s.ffill())

    out = df.sort_values(['ticker', 'date']).copy()
    out['close'] = out.groupby('ticker')['close'].transform(fill_one)
    return out.dropna(subset=['close']).reset_index(drop=True)


def run_data_qc(df, keys=('date', 'ticker'), price_field='close',
                expected_missing=('dividend',)):
    # the routine QC pass, self-contained
    out = df.copy()

    # fully duplicated rows: count and drop
    print('fully duplicated rows:', out.duplicated().sum())
    out = out.drop_duplicates()

    # key duplicates: flag for investigation, do not drop here
    dup = out[out.duplicated(subset=list(keys), keep=False)]
    print('key-duplicated rows:', len(dup))
    if len(dup):
        print(dup.sort_values(list(keys)).head(10))

    # fully missing column or ticker: upstream data issue
    all_missing_cols = [c for c in out.columns if out[c].isna().all()]
    print('fully missing columns:', all_missing_cols if all_missing_cols else 'none')
    per_ticker = out.groupby('ticker')[price_field].apply(lambda s: s.isna().all())
    dead = list(per_ticker[per_ticker].index)
    print('tickers with %s fully missing:' % price_field, dead if dead else 'none')

    # partial missing: compare rates against expectation
    rates = out.isna().mean().round(4)
    print(rates)
    for c, r in rates.items():
        if r > 0 and c not in expected_missing:
            print('check field:', c, 'missing rate:', r)

    return out
