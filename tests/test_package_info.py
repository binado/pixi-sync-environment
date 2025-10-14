"""Tests for the package_info module."""

from pixi_sync_environment.package_info import PackageInfo


class TestPackageInfoCreation:
    """Tests for PackageInfo dataclass instantiation."""

    def test_conda_package_creation(self):
        """Test creating a conda package with all fields."""
        pkg = PackageInfo(
            name="numpy",
            version="1.24.0",
            size_bytes=12345678,
            build="py310h1234567_0",
            kind="conda",
            source="conda-forge",
            is_explicit=True,
        )

        assert pkg.name == "numpy"
        assert pkg.version == "1.24.0"
        assert pkg.size_bytes == 12345678
        assert pkg.build == "py310h1234567_0"
        assert pkg.kind == "conda"
        assert pkg.source == "conda-forge"
        assert pkg.is_explicit is True

    def test_pypi_package_creation(self):
        """Test creating a PyPI package (build is None)."""
        pkg = PackageInfo(
            name="requests",
            version="2.31.0",
            size_bytes=234567,
            build=None,
            kind="pypi",
            source="https://pypi.org/simple",
            is_explicit=True,
        )

        assert pkg.name == "requests"
        assert pkg.version == "2.31.0"
        assert pkg.build is None
        assert pkg.kind == "pypi"

    def test_package_with_editable_field(self):
        """Test creating a package with is_editable field."""
        pkg = PackageInfo(
            name="my-package",
            version="0.1.0",
            size_bytes=1234,
            build=None,
            kind="pypi",
            source="https://pypi.org/simple",
            is_explicit=True,
            is_editable=True,
        )

        assert pkg.is_editable is True

    def test_package_without_editable_field(self):
        """Test that is_editable defaults to None."""
        pkg = PackageInfo(
            name="my-package",
            version="0.1.0",
            size_bytes=1234,
            build=None,
            kind="pypi",
            source="https://pypi.org/simple",
            is_explicit=True,
        )

        assert pkg.is_editable is None


class TestPackageInfoProperties:
    """Tests for PackageInfo properties."""

    def test_is_conda_package_property_true(self):
        """Test is_conda_package returns True for conda packages."""
        pkg = PackageInfo(
            name="python",
            version="3.10.0",
            size_bytes=12345,
            build="h1234567_0",
            kind="conda",
            source="conda-forge",
            is_explicit=True,
        )

        assert pkg.is_conda_package is True
        assert pkg.is_pypi_package is False

    def test_is_pypi_package_property_true(self):
        """Test is_pypi_package returns True for PyPI packages."""
        pkg = PackageInfo(
            name="requests",
            version="2.31.0",
            size_bytes=12345,
            build=None,
            kind="pypi",
            source="https://pypi.org/simple",
            is_explicit=True,
        )

        assert pkg.is_pypi_package is True
        assert pkg.is_conda_package is False


class TestGetPackageSpecStr:
    """Tests for get_package_spec_str method."""

    def test_get_package_spec_str_no_build(self):
        """Test package spec without build string (default)."""
        pkg = PackageInfo(
            name="numpy",
            version="1.24.0",
            size_bytes=12345,
            build="py310h1234567_0",
            kind="conda",
            source="conda-forge",
            is_explicit=True,
        )

        spec = pkg.get_package_spec_str()
        assert spec == "numpy=1.24.0"

    def test_get_package_spec_str_with_build(self):
        """Test package spec with build string included."""
        pkg = PackageInfo(
            name="numpy",
            version="1.24.0",
            size_bytes=12345,
            build="py310h1234567_0",
            kind="conda",
            source="conda-forge",
            is_explicit=True,
        )

        spec = pkg.get_package_spec_str(include_build=True)
        assert spec == "numpy=1.24.0=py310h1234567_0"

    def test_get_package_spec_str_none_build(self):
        """Test package spec when build is None (PyPI packages)."""
        pkg = PackageInfo(
            name="requests",
            version="2.31.0",
            size_bytes=12345,
            build=None,
            kind="pypi",
            source="https://pypi.org/simple",
            is_explicit=True,
        )

        spec = pkg.get_package_spec_str(include_build=False)
        assert spec == "requests=2.31.0"

    def test_get_package_spec_str_none_build_with_flag(self):
        """Test that None build is ignored even with include_build=True."""
        pkg = PackageInfo(
            name="requests",
            version="2.31.0",
            size_bytes=12345,
            build=None,
            kind="pypi",
            source="https://pypi.org/simple",
            is_explicit=True,
        )

        spec = pkg.get_package_spec_str(include_build=True)
        assert spec == "requests=2.31.0"

    def test_get_package_spec_str_special_characters(self):
        """Test package names with special characters (dashes, underscores)."""
        pkg = PackageInfo(
            name="python_abi",
            version="3.10",
            size_bytes=12345,
            build="cp310",
            kind="conda",
            source="conda-forge",
            is_explicit=True,
        )

        spec = pkg.get_package_spec_str()
        assert spec == "python_abi=3.10"

        pkg2 = PackageInfo(
            name="scikit-learn",
            version="1.3.0",
            size_bytes=12345,
            build="py310h1234567_0",
            kind="conda",
            source="conda-forge",
            is_explicit=True,
        )

        spec2 = pkg2.get_package_spec_str()
        assert spec2 == "scikit-learn=1.3.0"


class TestPackageInfoEquality:
    """Tests for PackageInfo equality comparisons."""

    def test_package_equality_identical(self):
        """Test that two packages with same data are equal."""
        pkg1 = PackageInfo(
            name="numpy",
            version="1.24.0",
            size_bytes=12345,
            build="py310h1234567_0",
            kind="conda",
            source="conda-forge",
            is_explicit=True,
        )

        pkg2 = PackageInfo(
            name="numpy",
            version="1.24.0",
            size_bytes=12345,
            build="py310h1234567_0",
            kind="conda",
            source="conda-forge",
            is_explicit=True,
        )

        assert pkg1 == pkg2

    def test_package_inequality_different_version(self):
        """Test that packages with different versions are not equal."""
        pkg1 = PackageInfo(
            name="numpy",
            version="1.24.0",
            size_bytes=12345,
            build="py310h1234567_0",
            kind="conda",
            source="conda-forge",
            is_explicit=True,
        )

        pkg2 = PackageInfo(
            name="numpy",
            version="1.25.0",
            size_bytes=12345,
            build="py310h1234567_0",
            kind="conda",
            source="conda-forge",
            is_explicit=True,
        )

        assert pkg1 != pkg2

    def test_package_inequality_different_name(self):
        """Test that packages with different names are not equal."""
        pkg1 = PackageInfo(
            name="numpy",
            version="1.24.0",
            size_bytes=12345,
            build="py310h1234567_0",
            kind="conda",
            source="conda-forge",
            is_explicit=True,
        )

        pkg2 = PackageInfo(
            name="pandas",
            version="1.24.0",
            size_bytes=12345,
            build="py310h1234567_0",
            kind="conda",
            source="conda-forge",
            is_explicit=True,
        )

        assert pkg1 != pkg2
