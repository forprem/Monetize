from __future__ import annotations

from io import BytesIO

from minio import Minio


class MinioExportWriter:
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ) -> None:
        self.bucket = bucket
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        found = self.client.bucket_exists(self.bucket)
        if not found:
            self.client.make_bucket(self.bucket)

    def write_export(self, tenant_id: str, dataset_code: str, job_id: str) -> str:
        object_name = f"{tenant_id}/{dataset_code}/{job_id}.csv"
        content = b"zip_code,signal_score,overall_score\n10001,81.2,79.4\n"
        payload = BytesIO(content)
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=object_name,
            data=payload,
            length=len(content),
            content_type="text/csv",
        )
        return f"s3://{self.bucket}/{object_name}"
