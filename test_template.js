
const sddState = { specs: [] };
function sddSlugify(text) {
    return (text || '').toString().toLowerCase().trim().replace(/[\s\W-]+/g, '-').replace(/^-+|-+$/g, '');
}
function sddBuildUniqueRequirementFilename(id, title, kind = 'req', parentId = null) {
    const slug = sddSlugify(title);
    let baseFilename = '';
    let folderPath = '';
    if (kind === 'rf') {
        const pId = parentId || 'REQ-XX';
        const pSlug = pId.toLowerCase();
        folderPath = \\/functional-requirements/\;
        baseFilename = \\_\\;
    } else {
        const reqSlug = \\_\\;
        folderPath = \\/\;
        baseFilename = reqSlug;
    }
    const existing = new Set((sddState.specs || []).map(spec => (spec.filename || '').toLowerCase()));
    let filename = \\\.md\;
    let suffix = 2;
    while (existing.has(filename.toLowerCase())) {
        filename = \\\_\.md\;
        suffix += 1;
    }
    return filename;
}
console.log(sddBuildUniqueRequirementFilename('REQ-1002', 'Teste'));

