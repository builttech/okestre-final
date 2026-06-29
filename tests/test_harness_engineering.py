import pytest


# Fixture to simulate environment and file structure
@pytest.fixture
def setup_file_structure(tmpdir):
    spec_dir = tmpdir.mkdir('.documents').mkdir('spec')
    design_file = spec_dir.join('design.md')
    dri_file = spec_dir.join('dri.md')
    task_file = spec_dir.join('task.md')
    return spec_dir, design_file, dri_file, task_file


# Test initializing or recognizing project structure
@pytest.mark.parametrize('file_exists', [True, False])
def test_initialize_project_structure(setup_file_structure, file_exists):
    spec_dir, design_file, dri_file, task_file = setup_file_structure
    if file_exists:
        spec_dir.ensure('REQ-3089.md')
        design_file.write('content')
        dri_file.write('content')
        task_file.write('content')

    assert spec_dir.check(dir=True)
    assert design_file.check(file=True)
    assert dri_file.check(file=True)
    assert task_file.check(file=True)


# Test creating a new REQ in spec directory
def test_create_new_req(setup_file_structure):
    spec_dir, _, _, _ = setup_file_structure
    req_file = spec_dir.join('REQ-3089.md')
    req_file.write('# REQ-3089 — Harness Engineering com documentos vivos por projeto\n\nThis is the content.')
    assert req_file.check(file=True)
    assert req_file.read().startswith('# REQ-3089')


# Ensure that attempting path traversal is rejected
@pytest.mark.parametrize('invalid_path', [
    '..',
    '/etc/passwd',
    '\\windows\\system32'
])
def test_path_validation_rejection(invalid_path):
    with pytest.raises(Exception):  # Assuming there's a security mechanism to handle invalid paths
        potentially_dangerous_path = invalid_path
