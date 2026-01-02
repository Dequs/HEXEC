import pathlib

def testVersionFile():
    repoRoot = pathlib.Path(__file__).resolve().parents[1]
    versionFile = repoRoot / "VERSION"
    assert versionFile.exists(), "VERSION file is missing"
    content = versionFile.read_text().strip()
    assert content != "", "VERSION file is empty"
