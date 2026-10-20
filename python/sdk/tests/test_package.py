import mcp_ext_filesystems


def test_package_reports_its_version() -> None:
    assert mcp_ext_filesystems.__version__ == "0.1.0"
