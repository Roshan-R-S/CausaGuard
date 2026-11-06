import copy
import json
from datetime import datetime, timezone

import pytest
from test_v052_policy import small_config

from causaguard.intervention_study import seal
from causaguard.v052 import study


@pytest.fixture(scope='module')
def recording(tmp_path_factory):
    directory = tmp_path_factory.mktemp('v052')
    config = small_config()
    path = directory/'config.json'
    path.write_text(config.model_dump_json())
    audit = directory/'audit.json'
    roles = {k:list(getattr(config,k+'_seeds')) for k in ('training','calibration','model','development')}
    roles.update(final_reserved=list(config.final_seeds),model_risk_offset=[s+3 for s in config.model_seeds],bootstrap=[config.bootstrap_seed])
    audit.write_text(json.dumps(dict(unique=True,hits=[],searched_files={'fixture':'test only'},roles=roles)))
    report = study.run_development(path,seed_audit_path=audit)
    return report


def test_development_exact_replay_and_counts(recording):
    assert study.replay_report(recording)['replay'] == 'matched'
    assert recording['resources']['forest_fits'] == 36
    assert recording['resources']['policy_case_evaluations'] == 1440


def test_final_rejects_without_generating_cases(recording,monkeypatch):
    def forbidden(*args,**kwargs):
        pytest.fail('generation before valid final preflight')
    monkeypatch.setattr(study,'make_cases',forbidden)
    with pytest.raises(ValueError):
        study.run_final(recording)
    damaged = copy.deepcopy(recording)
    damaged['selection']['selected_candidate'] = 'invented'
    with pytest.raises(ValueError):
        study.run_final(seal(damaged))
    damaged = copy.deepcopy(recording)
    damaged['identity']['pyproject'] = 'changed'
    with pytest.raises(ValueError):
        study.run_final(seal(damaged))


def test_resealed_recording_tamper_fails_replay(recording):
    damaged = copy.deepcopy(recording)
    damaged['evaluation']['iid']['decisions'][0]['rules_repair']['decisions_sha256'] = 'tampered'
    with pytest.raises(ValueError,match='differs'):
        study.replay_report(seal(damaged))


def test_model_identity_drift_refused(recording):
    damaged = copy.deepcopy(recording)
    damaged['training'][0]['models']['original_r05'] = 'changed'
    with pytest.raises(ValueError,match='model identity'):
        study.replay_report(seal(damaged))


def test_protocol_and_config_byte_identity(recording,monkeypatch):
    monkeypatch.setattr(study,'_current_identity',lambda value: {'drift':True})
    with pytest.raises(ValueError,match='identity changed'):
        study.validate_report(recording)


def test_approval_binding_and_date(recording):
    token = dict(statement=study.APPROVAL_STATEMENT,approved_by='unit test only',approved_at=datetime.now(timezone.utc).isoformat(),development_sha256=recording['sha256'],identity_sha256=recording['identity_sha256'],config_sha256=recording['config_sha256'])
    study.validate_approval(token,recording)
    for key,value in [('development_sha256','wrong'),('approved_at','2000-01-01T00:00:00+00:00'),('approved_by','')]:
        with pytest.raises(ValueError):
            study.validate_approval(token|{key:value},recording)


def test_exclusive_output_precedes_training(tmp_path,monkeypatch):
    out=tmp_path/'existing.json'
    out.write_text('preserve')
    monkeypatch.setattr(study,'run_development',lambda *a,**k: pytest.fail('must refuse first'))
    with pytest.raises(SystemExit):
        study.main(['locked-study','--phase','development','--config','experiments/v052.json','--output',str(out)])
    assert out.read_text() == 'preserve'

def test_eligible_final_requires_approval_and_exact_reconstruction(recording, monkeypatch):
    import numpy as np

    from causaguard.v052.inference import infer, select_candidate

    forged = copy.deepcopy(recording)
    for name, value in forged['cells'].items():
        x = np.asarray(value)
        x[..., 0] = .1 if name.startswith('f16') else 0
        x[..., 1] = .03
        x[..., 4] = 0
        forged['cells'][name] = x.tolist()
    config = small_config()
    forged['inference'] = infer(forged['cells'], config.bootstrap_replicates,
                                config.bootstrap_seed, .00625)
    forged['selection'] = select_candidate(forged['inference'])
    forged = seal(forged)
    assert forged['selection']['status'] == 'selected'
    original = study.make_cases

    def guarded(n, seed, *args, **kwargs):
        assert seed not in config.final_seeds, 'final cases generated before replay verified'
        return original(n, seed, *args, **kwargs)

    monkeypatch.setattr(study, 'make_cases', guarded)
    with pytest.raises(ValueError, match='approval'):
        study.run_final(forged)
    token = dict(statement=study.APPROVAL_STATEMENT, approved_by='test fixture',
                 approved_at=datetime.now(timezone.utc).isoformat(),
                 development_sha256=forged['sha256'], identity_sha256=forged['identity_sha256'],
                 config_sha256=forged['config_sha256'])
    with pytest.raises(ValueError, match='differs'):
        study.run_final(forged, token)
