from bioplatform.core.analysis_library import AnalysisLibrary


def test_analysis_library_catalog_contains_domains() -> None:
    lib = AnalysisLibrary()
    catalog = lib.catalog()
    ids = {c.func_id for c in catalog}
    assert 'python.stats.mean' in ids
    assert 'r.deseq2.differential_expression' in ids


def test_analysis_library_python_exec() -> None:
    lib = AnalysisLibrary()
    assert lib.execute_python('python.stats.mean', [1, 2, 3]) == 2
    assert round(lib.execute_python('python.genomics.gc_content', [20, 30, 100]), 2) == 50.0


def test_analysis_library_r_template() -> None:
    lib = AnalysisLibrary()
    tpl = lib.r_template('r.deseq2.differential_expression')
    assert 'DESeq2' in tpl
