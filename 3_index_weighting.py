# Demo of the common index weighting situations, once the sample list is
# fixed (columns: ticker, free_float_mcap, industry, layer = core/noncore).
# Situation 1: pool split -> core and noncore pools each get a fixed total
#              weight, names inside a pool are cap weighted
# Situation 2: stock caps by layer -> pin names above their cap, redistribute
#              the excess pro rata, repeat until stable
# Situation 3: segment cap on top of stock caps -> squeeze the noncore total
#              to its cap, hand the excess to core, re-apply stock caps
# Situation 4: industry-neutral weighting -> industry totals matched to the
#              universe, cap weighted inside each industry
# Weights are converted to weight factors at the end for delivery.
import pandas as pd


def pool_weight(snap, pool_weights={'core': 0.7, 'noncore': 0.3}):
    d = snap.copy()
    unknown = set(d['layer']) - set(pool_weights)
    if unknown:
        raise ValueError('layer values not in pool_weights: %s' % sorted(unknown))
    # pools absent from the sample: remaining pool weights renormalized to 1
    # (a policy choice - state it in the methodology)
    present = {k: v for k, v in pool_weights.items() if k in set(d['layer'])}
    scale = 1.0 / sum(present.values())
    pool_mcap = d.groupby('layer')['free_float_mcap'].transform('sum')
    d['weight'] = d['layer'].map(present) * scale * d['free_float_mcap'] / pool_mcap
    return d


def weight_with_caps(snap, caps={'core': 0.10, 'noncore': 0.04}, max_iter=200):
    d = snap.copy()
    cap_arr = d['layer'].map(caps).astype(float)
    if cap_arr.isna().any():
        raise ValueError('layer values missing from caps')
    cap_arr = cap_arr.values
    if cap_arr.sum() < 1 - 1e-12:
        raise ValueError('sum of caps < 1')
    w = d['free_float_mcap'].values / d['free_float_mcap'].sum()
    for _ in range(max_iter):
        over = w > cap_arr + 1e-12
        if not over.any():
            break
        excess = (w[over] - cap_arr[over]).sum()
        w[over] = cap_arr[over]
        free = ~over & (w < cap_arr - 1e-12)
        if not free.any():
            break
        w[free] += excess * w[free] / w[free].sum()
    # never return an invalid answer silently
    if (w > cap_arr + 1e-8).any() or abs(w.sum() - 1) > 1e-8:
        raise RuntimeError('capping did not converge to a valid solution')
    d['weight'] = w
    return d


def apply_segment_cap(d, caps={'core': 0.10, 'noncore': 0.04},
                      segment='noncore', total_cap=0.35, max_iter=50):
    d = d.copy()
    seg = (d['layer'] == segment).values
    cap_arr = d['layer'].map(caps).astype(float)
    if cap_arr.isna().any():
        raise ValueError('layer values missing from caps')
    cap_arr = cap_arr.values
    # feasibility: the other segment must be able to absorb 1 - total_cap
    if cap_arr[~seg].sum() < 1 - total_cap - 1e-12:
        raise ValueError('infeasible: caps outside the segment cannot absorb 1 - total_cap')
    w = d['weight'].values.copy()
    for _ in range(max_iter):
        seg_ok = w[seg].sum() <= total_cap + 1e-10
        caps_ok = (w <= cap_arr + 1e-10).all()
        if seg_ok and caps_ok and abs(w.sum() - 1) < 1e-8:
            d['weight'] = w
            return d
        if not seg_ok:
            excess = w[seg].sum() - total_cap
            w[seg] *= total_cap / w[seg].sum()
            receivers = ~seg & (w < cap_arr - 1e-12)
            if not receivers.any():
                raise RuntimeError('no room outside the segment to absorb the excess')
            w[receivers] += excess * w[receivers] / w[receivers].sum()
        # squeezing the segment can push other names over their stock caps
        over = w > cap_arr + 1e-12
        if over.any():
            excess = (w[over] - cap_arr[over]).sum()
            free = ~over & (w < cap_arr - 1e-12) & ~seg
            w[over] = cap_arr[over]
            if not free.any():
                raise RuntimeError('stock caps leave no room for the excess')
            w[free] += excess * w[free] / w[free].sum()
    raise RuntimeError('segment capping did not converge within max_iter')


def industry_neutral_weight(members_snap, universe_snap):
    # industry totals matched to the full universe, cap weighted inside
    target = universe_snap.groupby('industry')['free_float_mcap'].sum()
    target = target / target.sum()
    target = target.loc[target.index.isin(members_snap['industry'].unique())]
    target = target / target.sum()    # industries absent from the sample renormalized away
    d = members_snap.copy()
    ind_mcap = d.groupby('industry')['free_float_mcap'].transform('sum')
    d['weight'] = d['industry'].map(target) * d['free_float_mcap'] / ind_mcap
    return d


def weight_factor(d):
    # weight per unit of market cap, scaled so the largest factor is 1
    d = d.copy()
    wf = d['weight'] / d['free_float_mcap']
    d['weight_factor'] = wf / wf.max()
    return d
