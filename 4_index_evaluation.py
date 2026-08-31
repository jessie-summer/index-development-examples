# Demo of the numbers an index is usually evaluated on before launch.
# Situation 1: NAV backtest -> fixed units between rebalances (weights become
#              share counts at the rebalance close)
# Situation 2: performance -> annualized return / volatility / max drawdown,
#              tracking error against a benchmark
# Situation 3: turnover at each rebalance
# Situation 4: tradability -> investment capacity and days to build a position
# Situation 5: profiles -> weight distribution by industry, market cap bucket,
#              or listing venue
import numpy as np
import pandas as pd


def nav_backtest(prices, weight_book, base=1000.0):
    # prices: wide dataframe date x ticker, adjusted / total-return prices;
    # weight_book: {rebalance_date: weight series}
    # held names must exist in the price table with complete prices - both
    # cases raise instead of silently dropping the position from the value;
    # weights apply from the rebalance close onward (whether the weight book
    # itself was built point-in-time is up to the caller)
    rdates = sorted(weight_book.keys())
    not_in_index = [d for d in rdates if d not in prices.index]
    if not_in_index:
        raise ValueError('rebalance dates not in price index: %s' % not_in_index)
    for rd in rdates:
        held = weight_book[rd][weight_book[rd] > 0]
        absent = held.index.difference(prices.columns)
        if len(absent):
            raise ValueError('held names not in price table: %s' % list(absent))
    nav = pd.Series(index=prices.index, dtype=float)
    nav_val = base
    for i, rd in enumerate(rdates):
        end = rdates[i + 1] if i + 1 < len(rdates) else prices.index[-1]
        seg = prices.loc[rd:end]
        w = weight_book[rd].reindex(seg.columns).fillna(0.0)
        held = w.index[w > 0]
        gaps = seg[held].isna().any()
        if gaps.any():
            raise ValueError('missing prices for held names: %s' % list(gaps[gaps].index))
        units = w[held] * nav_val / seg[held].iloc[0]
        seg_nav = (seg[held] * units).sum(axis=1)
        nav.loc[seg.index] = seg_nav
        nav_val = seg_nav.iloc[-1]
    return nav.dropna()


def performance(nav, bench=None):
    # annualized return, annualized volatility, max drawdown in one place
    ret = nav.pct_change().dropna()
    out = {
        'ann_return': round((nav.iloc[-1] / nav.iloc[0]) ** (252 / (len(nav) - 1)) - 1, 4),
        'ann_vol': round(ret.std() * np.sqrt(252), 4),
        'max_drawdown': round((nav / nav.cummax() - 1).min(), 4),
    }
    if bench is not None:
        # overlapping dates only - a missing benchmark return is not a zero return
        bret = bench.pct_change().dropna()
        common = ret.index.intersection(bret.index)
        ex = ret.loc[common] - bret.loc[common]
        out['tracking_error'] = round(ex.std() * np.sqrt(252), 4)
    return out


def turnover(prev_w, curr_w):
    # sum(|dw|)/2, cross-checked against 1 - sum(min)
    aligned = pd.concat([prev_w.rename('prev'), curr_w.rename('curr')], axis=1).fillna(0.0)
    a = (aligned['curr'] - aligned['prev']).abs().sum() / 2
    b = 1 - np.minimum(aligned['prev'], aligned['curr']).sum()
    assert abs(a - b) < 1e-10
    return a


def capacity(w, adv, free_float_mcap, participation=0.1, build_days=5, ownership_cap=0.05):
    # smallest fund size that hits either the trading rule or the ownership rule;
    # the index of the min tells you which name is the bottleneck
    trading = adv * participation * build_days / w
    ownership = free_float_mcap * ownership_cap / w
    return {'trading_capacity': trading.min(), 'trading_bottleneck': trading.idxmin(),
            'ownership_capacity': ownership.min(), 'ownership_bottleneck': ownership.idxmin()}


def days_to_build(w, adv, fund_size, participation=0.1):
    days = fund_size * w / (adv * participation)
    return {'max_days': round(days.max(), 1), 'avg_days': round(days.mean(), 1),
            'slowest_name': days.idxmax()}


def weight_distribution(d, by='industry'):
    # works for industry, listing_venue, or any label column on the weighted sample
    return d.groupby(by)['weight'].sum().sort_values(ascending=False).round(4)


def mcap_distribution(d, bins=(0, 100, 300, 1000, float('inf'))):
    bucket = pd.cut(d['free_float_mcap'], bins)
    return d.groupby(bucket, observed=True)['weight'].sum().round(4)
