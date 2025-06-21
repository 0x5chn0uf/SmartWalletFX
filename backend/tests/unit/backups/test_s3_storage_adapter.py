from pathlib import Path

import pytest

# Skip test if optional dependency is missing

boto3 = pytest.importorskip("boto3")  # noqa: F401 – imported for availability check

from app.storage.s3 import S3StorageAdapter  # noqa: E402


class _DummyS3Client:  # minimal stub capturing calls
    def __init__(self):
        self.uploads: list[tuple[str, str, str]] = []
        self._objects: list[str] = []

    # boto3's high-level ``upload_file`` API
    def upload_file(self, filename: str, bucket: str, key: str):  # noqa: D401
        self.uploads.append((filename, bucket, key))
        self._objects.append(key)

    # paginator stub for list_objects_v2
    def get_paginator(self, name: str):  # noqa: D401
        assert name == "list_objects_v2"

        class _Paginator:  # pylint: disable=too-few-public-methods
            def __init__(self, objects: list[str]):
                self._objects = objects

            def paginate(self, *, Bucket: str, Prefix: str = ""):
                # The bucket is passed to paginate, so we don't need to assert
                # against a stored bucket name.
                del Bucket  # Unused, but part of the boto3 interface
                filtered = [k for k in self._objects if k.startswith(Prefix)]
                yield {"Contents": [{"Key": k} for k in filtered]}

        return _Paginator(self._objects)


def test_s3_storage_adapter_save_and_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    dummy = _DummyS3Client()
    adapter = S3StorageAdapter(bucket="test-bucket", client=dummy)

    # prepare file
    file_path = tmp_path / "hello.txt"
    file_path.write_text("hello world")

    uri = adapter.save(file_path)
    assert uri == "s3://test-bucket/hello.txt"

    # ensure client captured upload
    assert dummy.uploads[0][1:] == ("test-bucket", "hello.txt")

    # list returns the key
    assert adapter.list() == ["hello.txt"]
    # list with prefix
    assert adapter.list(prefix="hell") == ["hello.txt"]
    assert adapter.list(prefix="nope") == []
