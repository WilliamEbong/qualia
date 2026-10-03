from qualia import workspace


def test_blank_env_setting_does_not_consume_next_line(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace, 'REPO', tmp_path)
    monkeypatch.delenv('QUALIA_HOME', raising=False)
    monkeypatch.delenv('QUALIA_PORT', raising=False)
    (tmp_path / '.env').write_text('QUALIA_HOME=\nQUALIA_PORT=8766\nTYPESAFE_API_KEY=unused-test\n')
    assert workspace.local_setting('QUALIA_HOME') == ''
    assert workspace.local_setting('QUALIA_PORT') == '8766'
    monkeypatch.setenv('QUALIA_PORT', '8767')
    assert workspace.local_setting('QUALIA_PORT') == '8767'
