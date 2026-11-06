"""Reconstruct v052 planning variances from historical development only."""
import json
from pathlib import Path
from statistics import NormalDist

import numpy as np

from causaguard.intervention_env import ACTIONS, Observation, make_cases, potential_outcomes
from causaguard.intervention_policy import design, fixed_mean, refit_original
from causaguard.provenance import policy_fingerprint
from causaguard.v052.policy import select_original


def main():
    old = json.loads(Path('artifacts/v051/development-frozen.json').read_text())
    cfg = old['config']
    result = old['results']['iid']
    obs = [Observation(**c['observation']) for c in result['cases']]
    outcomes = result['potential_outcomes']
    matrices = {p: [] for p in ('f16_raw_r05', 'f16_cal_r05', 'rules_repair', 'original_r05')}
    for i, (ts, ms) in enumerate(zip(cfg['training_seeds'], cfg['model_seeds'], strict=True)):
        train = make_cases(cfg['train_n'], ts)
        base = refit_original([c.observation for c in train], potential_outcomes(train), ms, cfg['trees'])
        assert policy_fingerprint(base) == old['training'][i]['models']['original']
        x = design(obs, False)
        reward = {a: fixed_mean(base.reward_models[a], x)[:, 0] for a in ACTIONS}
        risk = {a: fixed_mean(base.risk_models[a], x)[:, 0] for a in ACTIONS}
        decisions = dict(result['decisions'][i])
        decisions['original_r05'] = select_original(obs, reward, risk)
        for p in matrices:
            matrices[p].append(np.array([o[a]['utility'] for o, a in zip(outcomes, decisions[p], strict=True)]).reshape(8, 250).mean(axis=1))
    contrasts = {}
    for candidate in ('f16_raw_r05', 'f16_cal_r05'):
        for baseline in ('original_r05', 'rules_repair'):
            x = np.array(matrices[candidate]) - matrices[baseline]
            r, s = x.shape
            residual = x-x.mean(1)[:,None]-x.mean(0)[None,:]+x.mean()
            ve = (residual**2).sum()/((r-1)*(s-1))
            vr = (s*x.mean(1).var(ddof=1)-ve)/s
            vs = (r*x.mean(0).var(ddof=1)-ve)/r
            contrasts[candidate+'-'+baseline] = dict(mean=float(x.mean()), training=max(0,float(vr)), evaluation=max(0,float(vs)), residual=float(ve), untruncated_evaluation=float(vs))
    envelope = {k:max(v[k] for v in contrasts.values()) for k in ('training','evaluation','residual')}
    normal = NormalDist()
    tables = []
    for multiplier,alpha in ((1,.0125),(2,.0125),(4,.0125),(2,.00625)):
        se = (multiplier*(envelope['training']/32+envelope['evaluation']/64+envelope['residual']/(32*64)))**.5
        tables.append(dict(variance_multiplier=multiplier,alpha=alpha,se=se,power={str(d):normal.cdf((d-.02)/se-normal.inv_cdf(1-alpha)) for d in (.03,.04,.06)}))
    payload = dict(historical_development_sha256=old['sha256'], contrasts=contrasts,envelope=envelope,power=tables,audit_forest_fits=40,prior_exploratory_audit_forest_fits=80,limitations='Five historical replicas; sensitivity envelope is not a variance confidence bound. Marginal normal utility power, not joint or safety power.')
    with Path('docs/v052-power.json').open('x') as f:
        json.dump(payload,f,indent=2)
    print(json.dumps(payload,indent=2))


if __name__ == '__main__':
    main()
