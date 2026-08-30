# Demo of the common index selection situations, on a snapshot dataframe
# (columns: ticker, free_float_mcap, industry, plus factor fields as needed).
# Situation 1: direct selection -> sort one field, take the top n
# Situation 2: factor selection -> winsorize / rank the factors, combine into
#              one score, take the top n
# Situation 3: industry-loop selection -> each industry gets a quota of
#              floor(n * industry share), quotas filled by rank, the shortfall
#              left by flooring topped up with the largest remaining names
import pandas as pd


def select_direct(snap, n, by='free_float_mcap'):
    return snap.nlargest(n, by)['ticker'].tolist()


# ---- factor helpers for scenario 2 ----

def winsorize(s, limit=0.025):
    return s.clip(s.quantile(limit), s.quantile(1 - limit))


def z_score(s, cap=3):
    z = (s - s.mean()) / s.std()
    return z.clip(-cap, cap)


def pct_rank(s, ascending=True):
    return s.rank(pct=True, ascending=ascending)


def composite_score(df, factors, weights=None):
    # factors oriented so that higher = better before they come in
    # policy: a name missing any factor gets no score - do not let a partial
    # sum pass as a valid score
    if weights is None:
        weights = [1 / len(factors)] * len(factors)
    ranks = pd.concat([pct_rank(winsorize(df[f])) for f in factors], axis=1)
    score = (ranks * weights).sum(axis=1)
    score[ranks.isna().any(axis=1)] = float('nan')
    return score


def select_by_score(snap, n, factors, weights=None):
    # names without a full score are excluded (nlargest skips NaN)
    d = snap.copy()
    d['score'] = composite_score(d, factors, weights)
    return d.nlargest(n, 'score')['ticker'].tolist()


# ---- scenario 3 ----

def select_industry_loop(snap, n, by='free_float_mcap'):
    # e.g. n=50, industry shares 0.52/0.31/0.17 -> quotas floor to 26/15/8,
    # one seat left over -> the largest unselected name takes it
    d = snap.copy()
    share = d.groupby('industry')[by].sum() / d[by].sum()
    quota = (share * n).astype(int)
    picked = []
    for ind, q in quota.items():
        picked += d.loc[d['industry'] == ind].nlargest(q, by)['ticker'].tolist()
    rest = d.loc[~d['ticker'].isin(picked)]
    picked += rest.nlargest(n - len(picked), by)['ticker'].tolist()
    return sorted(picked)
