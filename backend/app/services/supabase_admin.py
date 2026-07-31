# File: /backend/app/services/supabase_admin.py
# Purpose: Provides trusted backend-only access to Supabase
# PostgREST, database functions, and private Storage objects.

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from app.core.config import Settings
from app.services.file_extraction import (
    ExtractedChunk,
    ExtractedDocument,
)


@dataclass(frozen=True)
class ClaimedProcessingJob:
    """One file-processing job claimed by a worker."""

    processing_job_id: UUID
    study_file_id: UUID


@dataclass(frozen=True)
class RecoveredProcessingJobs:
    """Counts returned after recovering abandoned jobs."""

    requeued_count: int
    failed_count: int


class SupabaseAdminError(RuntimeError):
    """Raised when a trusted Supabase operation fails."""


class SupabaseAdminService:
    """Minimal trusted Supabase REST and Storage client.

    This service uses the backend-only Supabase secret key.
    It must never be imported into frontend code or exposed
    through a NEXT_PUBLIC environment variable.
    """

    def __init__(
        self,
        settings: Settings,
    ) -> None:
        self._settings = settings

    @property
    def _postgrest_headers(
        self,
    ) -> dict[str, str]:
        """Return headers for trusted PostgREST requests."""

        return {
            "apikey": (
                self._settings.supabase_secret_key
            ),
            "Accept": "application/json",
        }

    @property
    def _storage_headers(
        self,
    ) -> dict[str, str]:
        """Return headers for trusted Storage requests."""

        return {
            "apikey": (
                self._settings.supabase_secret_key
            ),
            "Accept": "application/octet-stream",
        }

    async def get_study_file(
        self,
        file_id: UUID,
    ) -> dict[str, Any] | None:
        """Return one study-file row by its UUID."""

        endpoint = (
            f"{self._settings.supabase_url}"
            "/rest/v1/study_files"
        )

        params = {
            "select": (
                "id,"
                "user_id,"
                "subject_id,"
                "original_filename,"
                "storage_path,"
                "mime_type,"
                "size_bytes,"
                "processing_status"
            ),
            "id": f"eq.{file_id}",
            "limit": "1",
        }

        try:
            async with httpx.AsyncClient(
                timeout=(
                    self._settings
                    .request_timeout_seconds
                ),
            ) as client:
                response = await client.get(
                    endpoint,
                    params=params,
                    headers=self._postgrest_headers,
                )

        except httpx.TimeoutException as error:
            raise SupabaseAdminError(
                "The study-file lookup timed out.",
            ) from error

        except httpx.RequestError as error:
            raise SupabaseAdminError(
                "The study-file lookup could not "
                "reach Supabase.",
            ) from error

        if response.status_code != 200:
            raise SupabaseAdminError(
                "Unable to retrieve the study-file record. "
                f"Supabase returned {response.status_code}: "
                f"{response.text}"
            )

        try:
            rows = response.json()

        except ValueError as error:
            raise SupabaseAdminError(
                "Supabase returned invalid JSON for the "
                "study-file lookup.",
            ) from error

        if not isinstance(
            rows,
            list,
        ):
            raise SupabaseAdminError(
                "Supabase returned an invalid "
                "study-file response.",
            )

        if not rows:
            return None

        row = rows[0]

        if not isinstance(
            row,
            dict,
        ):
            raise SupabaseAdminError(
                "Supabase returned an invalid "
                "study-file row.",
            )

        return row

    async def get_processing_job(
        self,
        file_id: UUID,
    ) -> dict[str, Any] | None:
        """Return the processing job connected to a study file."""

        endpoint = (
            f"{self._settings.supabase_url}"
            "/rest/v1/file_processing_jobs"
        )

        params = {
            "select": (
                "id,"
                "user_id,"
                "study_file_id,"
                "status,"
                "attempt_count,"
                "started_at,"
                "completed_at,"
                "error_code,"
                "error_message"
            ),
            "study_file_id": f"eq.{file_id}",
            "limit": "1",
        }

        try:
            async with httpx.AsyncClient(
                timeout=(
                    self._settings
                    .request_timeout_seconds
                ),
            ) as client:
                response = await client.get(
                    endpoint,
                    params=params,
                    headers=self._postgrest_headers,
                )

        except httpx.TimeoutException as error:
            raise SupabaseAdminError(
                "The processing-job lookup timed out.",
            ) from error

        except httpx.RequestError as error:
            raise SupabaseAdminError(
                "The processing-job lookup could not "
                "reach Supabase.",
            ) from error

        if response.status_code != 200:
            raise SupabaseAdminError(
                "Unable to retrieve the processing job. "
                f"Supabase returned {response.status_code}: "
                f"{response.text}"
            )

        try:
            rows = response.json()

        except ValueError as error:
            raise SupabaseAdminError(
                "Supabase returned invalid JSON for the "
                "processing-job lookup.",
            ) from error

        if not isinstance(
            rows,
            list,
        ):
            raise SupabaseAdminError(
                "Supabase returned an invalid "
                "processing-job response.",
            )

        if not rows:
            return None

        row = rows[0]

        if not isinstance(
            row,
            dict,
        ):
            raise SupabaseAdminError(
                "Supabase returned an invalid "
                "processing-job row.",
            )

        return row

    async def download_private_object(
        self,
        storage_path: str,
    ) -> bytes:
        """Download one private object through the backend."""

        normalized_path = (
            storage_path
            .strip()
            .lstrip("/")
        )

        path_parts = (
            normalized_path.split("/")
            if normalized_path
            else []
        )

        if (
            not normalized_path
            or not path_parts
            or any(
                part in {
                    "",
                    ".",
                    "..",
                }
                for part in path_parts
            )
        ):
            raise SupabaseAdminError(
                "The stored object path is invalid.",
            )

        encoded_bucket = quote(
            self._settings
            .study_materials_bucket,
            safe="",
        )

        encoded_path = quote(
            normalized_path,
            safe="/",
        )

        endpoint = (
            f"{self._settings.supabase_url}"
            "/storage/v1/object/authenticated/"
            f"{encoded_bucket}/{encoded_path}"
        )

        try:
            async with httpx.AsyncClient(
                timeout=(
                    self._settings
                    .request_timeout_seconds
                ),
                follow_redirects=True,
            ) as client:
                response = await client.get(
                    endpoint,
                    headers=self._storage_headers,
                )

        except httpx.TimeoutException as error:
            raise SupabaseAdminError(
                "The private file download timed out.",
            ) from error

        except httpx.RequestError as error:
            raise SupabaseAdminError(
                "The private file download could not "
                "reach Supabase.",
            ) from error

        if response.status_code == 404:
            raise SupabaseAdminError(
                "The private Storage object was not found.",
            )

        if response.status_code in {
            401,
            403,
        }:
            raise SupabaseAdminError(
                "Supabase rejected the backend "
                "Storage credentials.",
            )

        if response.status_code != 200:
            raise SupabaseAdminError(
                "Unable to download the private "
                "Storage object. "
                f"Supabase returned {response.status_code}: "
                f"{response.text}"
            )

        payload = response.content

        if not payload:
            raise SupabaseAdminError(
                "The downloaded private file is empty.",
            )

        if (
            len(payload)
            > self._settings
            .max_processing_file_bytes
        ):
            raise SupabaseAdminError(
                "The downloaded file exceeds the "
                "backend processing limit.",
            )

        return payload

    async def _call_rpc(
        self,
        function_name: str,
        payload: dict[str, Any],
    ) -> None:
        """Call one trusted Supabase function."""

        normalized_function_name = (
            function_name.strip()
        )

        if not normalized_function_name:
            raise SupabaseAdminError(
                "The Supabase function name is required.",
            )

        endpoint = (
            f"{self._settings.supabase_url}"
            f"/rest/v1/rpc/{normalized_function_name}"
        )

        headers = {
            **self._postgrest_headers,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(
                timeout=(
                    self._settings
                    .request_timeout_seconds
                ),
            ) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                )

        except httpx.TimeoutException as error:
            raise SupabaseAdminError(
                f"The {normalized_function_name} "
                "request timed out.",
            ) from error

        except httpx.RequestError as error:
            raise SupabaseAdminError(
                f"The {normalized_function_name} request "
                "could not reach Supabase.",
            ) from error

        if response.status_code not in {
            200,
            201,
            204,
        }:
            raise SupabaseAdminError(
                "Supabase function "
                f"{normalized_function_name} failed. "
                f"Supabase returned {response.status_code}: "
                f"{response.text}"
            )

    async def _call_rpc_json(
        self,
        function_name: str,
        payload: dict[str, Any],
    ) -> Any:
        """Call a trusted RPC and return its JSON response."""

        normalized_function_name = (
            function_name.strip()
        )

        if not normalized_function_name:
            raise SupabaseAdminError(
                "The Supabase function name is required.",
            )

        endpoint = (
            f"{self._settings.supabase_url}"
            f"/rest/v1/rpc/{normalized_function_name}"
        )

        headers = {
            **self._postgrest_headers,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(
                timeout=(
                    self._settings
                    .request_timeout_seconds
                ),
            ) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                )

        except httpx.TimeoutException as error:
            raise SupabaseAdminError(
                f"The {normalized_function_name} "
                "request timed out.",
            ) from error

        except httpx.RequestError as error:
            raise SupabaseAdminError(
                f"The {normalized_function_name} request "
                "could not reach Supabase.",
            ) from error

        if response.status_code not in {
            200,
            201,
            204,
        }:
            raise SupabaseAdminError(
                "Supabase function "
                f"{normalized_function_name} failed. "
                f"Supabase returned {response.status_code}: "
                f"{response.text}"
            )

        if (
            response.status_code == 204
            or not response.content
        ):
            return None

        try:
            return response.json()

        except ValueError as error:
            raise SupabaseAdminError(
                "Supabase function "
                f"{normalized_function_name} returned "
                "invalid JSON.",
            ) from error

    async def claim_next_processing_job(
        self,
    ) -> ClaimedProcessingJob | None:
        """Atomically claim the next queued processing job."""

        response_data = await self._call_rpc_json(
            function_name=(
                "claim_next_file_processing_job"
            ),
            payload={},
        )

        if (
            response_data is None
            or response_data == ""
            or response_data == []
        ):
            return None

        if (
            not isinstance(
                response_data,
                list,
            )
            or len(response_data) != 1
            or not isinstance(
                response_data[0],
                dict,
            )
        ):
            raise SupabaseAdminError(
                "Supabase returned an invalid "
                "processing-job claim response.",
            )

        row = response_data[0]

        try:
            processing_job_id = UUID(
                str(
                    row["processing_job_id"],
                ),
            )

            study_file_id = UUID(
                str(
                    row["study_file_id"],
                ),
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            raise SupabaseAdminError(
                "Supabase returned invalid IDs for the "
                "claimed processing job.",
            ) from error

        return ClaimedProcessingJob(
            processing_job_id=processing_job_id,
            study_file_id=study_file_id,
        )

    async def recover_stale_processing_jobs(
        self,
        stale_after_minutes: int = 30,
        max_attempts: int = 3,
    ) -> RecoveredProcessingJobs:
        """Recover abandoned jobs through the trusted RPC."""

        if stale_after_minutes < 1:
            raise ValueError(
                "stale_after_minutes must be at least 1.",
            )

        if max_attempts < 1:
            raise ValueError(
                "max_attempts must be at least 1.",
            )

        response_data = await self._call_rpc_json(
            function_name=(
                "recover_stale_file_processing_jobs"
            ),
            payload={
                "p_stale_after_minutes": (
                    stale_after_minutes
                ),
                "p_max_attempts": (
                    max_attempts
                ),
            },
        )

        if (
            not isinstance(
                response_data,
                list,
            )
            or len(response_data) != 1
            or not isinstance(
                response_data[0],
                dict,
            )
        ):
            raise SupabaseAdminError(
                "Supabase returned an invalid stale-job "
                "recovery response.",
            )

        row = response_data[0]

        try:
            requeued_count = int(
                row["requeued_count"],
            )

            failed_count = int(
                row["failed_count"],
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            raise SupabaseAdminError(
                "Supabase returned invalid stale-job "
                "recovery counts.",
            ) from error

        if (
            requeued_count < 0
            or failed_count < 0
        ):
            raise SupabaseAdminError(
                "Supabase returned negative stale-job "
                "recovery counts.",
            )

        return RecoveredProcessingJobs(
            requeued_count=(
                requeued_count
            ),
            failed_count=(
                failed_count
            ),
        )

    async def start_processing(
        self,
        file_id: UUID,
    ) -> None:
        """Move a queued file into the reading state."""

        await self._call_rpc(
            function_name=(
                "start_study_file_processing"
            ),
            payload={
                "p_study_file_id": str(
                    file_id,
                ),
            },
        )

    async def mark_indexing(
        self,
        file_id: UUID,
    ) -> None:
        """Move a study file from reading to indexing."""

        await self._call_rpc(
            function_name=(
                "mark_study_file_indexing"
            ),
            payload={
                "p_study_file_id": str(
                    file_id,
                ),
            },
        )

    async def complete_processing(
        self,
        file_id: UUID,
        document: ExtractedDocument,
        chunks: list[ExtractedChunk],
    ) -> None:
        """Persist extracted text and complete processing."""

        if not chunks:
            raise SupabaseAdminError(
                "At least one extracted chunk is required.",
            )

        serialized_chunks = [
            {
                "chunk_index": (
                    chunk.chunk_index
                ),
                "content": (
                    chunk.content
                ),
                "locator_type": (
                    chunk.locator_type
                ),
                "locator_label": (
                    chunk.locator_label
                ),
                "token_count": (
                    chunk.token_count
                ),
                "metadata": (
                    chunk.metadata
                ),
            }
            for chunk in chunks
        ]

        await self._call_rpc(
            function_name=(
                "complete_study_file_processing"
            ),
            payload={
                "p_study_file_id": str(
                    file_id,
                ),
                "p_extracted_text": (
                    document.extracted_text
                ),
                "p_page_count": (
                    document.page_count
                ),
                "p_slide_count": (
                    document.slide_count
                ),
                "p_sheet_count": (
                    document.sheet_count
                ),
                "p_character_count": (
                    document.character_count
                ),
                "p_extraction_metadata": (
                    document.metadata
                ),
                "p_chunks": (
                    serialized_chunks
                ),
            },
        )

    async def fail_processing(
        self,
        file_id: UUID,
        error_code: str,
        error_message: str,
    ) -> None:
        """Mark a file-processing attempt as failed."""

        normalized_error_code = (
            error_code.strip()
            or "PROCESSING_FAILED"
        )

        normalized_error_message = (
            error_message.strip()
            or "The file could not be processed."
        )

        await self._call_rpc(
            function_name=(
                "fail_study_file_processing"
            ),
            payload={
                "p_study_file_id": str(
                    file_id,
                ),
                "p_error_code": (
                    normalized_error_code
                ),
                "p_error_message": (
                    normalized_error_message
                ),
            },
        )