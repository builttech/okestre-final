import pytest

@pytest.mark.parametrize('initialization,required_structure', [
    (True, ['.documents/spec/', '.documents/design/design.md', '.documents/dri/dri.md', '.documents/task/task.md']),
])

async def test_initialize_harness_engineering(initialization, required_structure, harness_api):
    if initialization:
        await harness_api.initialize()
    existing_structure = await harness_api.check_structure()
    assert set(required_structure) == set(existing_structure)


async def test_ctr3089_002_create_new_req(harness_api, req_details):
    await harness_api.create_req(req_details)
    assert await harness_api.has_file(f".documents/spec/{req_details['id']}.md")


async def test_list_multiple_reqs(harness_api):
    req_ids = await harness_api.list_reqs()
    assert len(req_ids) > 0 and all('REQ-' in id for id in req_ids)


async def test_open_and_save_single_req(harness_api, req_id):
    original_content = await harness_api.read_req(req_id)
    modified_content = original_content + '\nAdditional content for testing.'
    await harness_api.save_req(req_id, modified_content)
    assert await harness_api.read_req(req_id) == modified_content


async def test_open_and_save_design_doc(harness_api):
    original_design_content = await harness_api.read_project_document('design')
    modified_design_content = original_design_content + '\nDesign modifications for test.'
    await harness_api.save_project_document('design', modified_design_content)
    assert (await harness_api.read_project_document('design')) == modified_design_content


async def test_open_and_save_dri_doc(harness_api):
    original_dri_content = await harness_api.read_project_document('dri')
    modified_dri_content = original_dri_content + '\nDRI modifications for test.'
    await harness_api.save_project_document('dri', modified_dri_content)
    assert (await harness_api.read_project_document('dri')) == modified_dri_content


async def test_read_and_update_tasks(harness_api):
    tasks = await harness_api.read_tasks()
    tasks_updated = tasks.replace('- [ ]', '- [x]')
    await harness_api.update_tasks(tasks_updated)
    assert '- [x]' in (await harness_api.read_tasks())


async def test_execute_derivation_from_selected_task(harness_api, selected_task):
    execution_instructions = await harness_api.derive_execution_from_task(selected_task)
    assert 'REQ-' in execution_instructions


async def test_block_path_traversal(harness_api):
    with pytest.raises(SecurityError):
        await harness_api.validate_path("../invalid/access")


async def test_legacy_specs_accessibility(harness_api):
    legacy_specs_list = await harness_api.list_legacy_specs()
    assert len(legacy_specs_list) > 0


async def test_textual_changes_reflecting_structure(harness_api):
    harness_texts = await harness_api.fetch_texts()
    assert '.documents/spec/' in harness_texts and '.documents/task/' in harness_texts