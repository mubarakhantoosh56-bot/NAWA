"""Files API routes for MVP RAG ingestion."""

import logging
import tempfile
from pathlib import Path
from uuid import UUID

import asyncpg
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)

from app.core.config import settings
from app.core.dependencies import AuthContext
from app.core.permissions import has_permission, require_permission
from app.core.role_permissions import (
    CEO_WORKSPACE_PERMISSION,
    OPERATIONAL_FORM_READ_PERMISSION,
    OPERATIONAL_FORM_SUBMIT_PERMISSION,
    visible_department_types,
)
from app.models.request import ConfirmDraftRequest
from app.models.response import (
    DraftConfirmResponse,
    EventDraftListResponse,
    EventDraftResponse,
    FileDetailResponse,
    FileListResponse,
    FileResponse,
)
from app.services.file_ingestion_service import FileIngestionService
from app.services.operational_event_draft_service import OperationalEventDraftService

router = APIRouter(prefix="/files", tags=["Files"])
logger = logging.getLogger(__name__)


async def get_draft_service(request: Request) -> OperationalEventDraftService:
    """Return an OperationalEventDraftService backed by the app database pool."""
    pool = getattr(request.app.state, "auth_db_pool", None)
    if pool is None:
        if not settings.DATABASE_URL:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Draft service unavailable",
            )
        pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=5,
        )
        request.app.state.auth_db_pool = pool
    return OperationalEventDraftService(pool)


async def get_file_ingestion_service(request: Request) -> FileIngestionService:
    """Return a FileIngestionService backed by the app database pool."""
    pool = getattr(request.app.state, "auth_db_pool", None)
    if pool is None:
        if not settings.DATABASE_URL:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="File service unavailable",
            )
        pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=5,
        )
        request.app.state.auth_db_pool = pool

    return FileIngestionService(pool)


@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    department_id: UUID | None = None,
    auth_context: AuthContext = Depends(require_permission("files.upload")),
    file_service: FileIngestionService = Depends(get_file_ingestion_service),
) -> FileResponse:
    """Upload and synchronously ingest one MVP text-like file."""
    try:
        await _validate_file_department_scope(
            file_service=file_service,
            auth_context=auth_context,
            department_id=department_id,
        )
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                temp_file.write(chunk)

        try:
            result = await file_service.ingest_file(
                company_id=UUID(auth_context.company_id),
                uploaded_by_user_id=UUID(auth_context.user_id),
                source_path=temp_path,
                filename=file.filename or "upload",
                content_type=file.content_type or "",
                department_id=department_id,
            )
        finally:
            temp_path.unlink(missing_ok=True)

        file_record = result["file"]
        if file_record.get("status") == "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(result.get("error") or "file ingestion failed"),
            )
        return FileResponse.model_validate(file_record)
    except HTTPException:
        raise
    except ValueError as exc:
        logger.info("File upload failed with safe domain error")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("File upload endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File service unavailable",
        ) from exc


@router.get("", response_model=FileListResponse)
async def list_files(
    department_id: UUID | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    auth_context: AuthContext = Depends(require_permission("files.read")),
    file_service: FileIngestionService = Depends(get_file_ingestion_service),
) -> FileListResponse:
    """List files for the authenticated tenant."""
    try:
        scoped_department_ids = await _resolve_readable_department_ids(
            file_service=file_service,
            auth_context=auth_context,
            department_id=department_id,
        )
        files = await file_service.list_files(
            company_id=UUID(auth_context.company_id),
            department_id=department_id,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
        if scoped_department_ids is not None:
            files = [
                file
                for file in files
                if file.get("department_id") in scoped_department_ids
            ]
        return FileListResponse.model_validate({"files": files})
    except ValueError as exc:
        logger.info("List files failed with safe domain error")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("List files endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File service unavailable",
        ) from exc


async def _validate_file_department_scope(
    file_service: FileIngestionService,
    auth_context: AuthContext,
    department_id: UUID | None,
) -> None:
    if department_id is None:
        if has_permission(auth_context.permissions, CEO_WORKSPACE_PERMISSION):
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Department-scoped file upload required",
        )

    department = await file_service.department_repo.get_by_id(
        company_id=UUID(auth_context.company_id),
        department_id=department_id,
    )
    if department is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid department access",
        )
    required_permission = f"agents.{department['department_type']}.use"
    if not has_permission(auth_context.permissions, required_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing permission",
        )


async def _resolve_readable_department_ids(
    file_service: FileIngestionService,
    auth_context: AuthContext,
    department_id: UUID | None,
) -> set[UUID] | None:
    visible_types = visible_department_types(auth_context.permissions)
    if visible_types is None:
        return None

    departments = await file_service.department_repo.list_by_company(UUID(auth_context.company_id))
    visible_ids = {
        department["id"]
        for department in departments
        if str(department.get("department_type") or "") in visible_types
    }
    if department_id is not None and department_id not in visible_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid department access",
        )
    return visible_ids


@router.get("/{file_id}", response_model=FileDetailResponse)
async def get_file(
    file_id: UUID,
    auth_context: AuthContext = Depends(require_permission("files.read")),
    file_service: FileIngestionService = Depends(get_file_ingestion_service),
) -> FileDetailResponse:
    """Return safe file metadata for the authenticated tenant."""
    try:
        file_record = await file_service.get_file(
            company_id=UUID(auth_context.company_id),
            file_id=file_id,
        )
        if file_record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )
        return FileDetailResponse.model_validate(file_record)
    except HTTPException:
        raise
    except ValueError as exc:
        logger.info("Get file failed with safe domain error")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Get file endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File service unavailable",
        ) from exc


@router.get("/{file_id}/event-drafts", response_model=EventDraftListResponse)
async def list_file_event_drafts(
    file_id: UUID,
    auth_context: AuthContext = Depends(require_permission(OPERATIONAL_FORM_READ_PERMISSION)),
    draft_service: OperationalEventDraftService = Depends(get_draft_service),
) -> EventDraftListResponse:
    """Return pending AI-proposed event drafts for one file (company-scoped)."""
    try:
        drafts = await draft_service.list_pending(
            company_id=UUID(auth_context.company_id),
            file_id=file_id,
        )
        return EventDraftListResponse(file_id=file_id, drafts=drafts)
    except Exception as exc:
        logger.error("List event drafts failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Draft service unavailable",
        ) from exc


@router.post(
    "/{file_id}/event-drafts/{draft_id}/confirm",
    response_model=DraftConfirmResponse,
    status_code=status.HTTP_200_OK,
)
async def confirm_event_draft(
    file_id: UUID,
    draft_id: UUID,
    body: ConfirmDraftRequest,
    auth_context: AuthContext = Depends(require_permission(OPERATIONAL_FORM_SUBMIT_PERMISSION)),
    draft_service: OperationalEventDraftService = Depends(get_draft_service),
) -> DraftConfirmResponse:
    """Confirm one pending draft. Creates one operational_event with full file provenance."""
    try:
        result = await draft_service.confirm(
            company_id=UUID(auth_context.company_id),
            file_id=file_id,
            draft_id=draft_id,
            confirmed_by_user_id=UUID(auth_context.user_id),
            user_edits={k: v for k, v in body.model_dump().items() if v is not None},
        )
        return DraftConfirmResponse(
            draft=result["draft"],
            event=result["event"],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Confirm event draft failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Draft service unavailable",
        ) from exc


@router.post(
    "/{file_id}/event-drafts/{draft_id}/reject",
    response_model=EventDraftResponse,
    status_code=status.HTTP_200_OK,
)
async def reject_event_draft(
    file_id: UUID,
    draft_id: UUID,
    auth_context: AuthContext = Depends(require_permission(OPERATIONAL_FORM_SUBMIT_PERMISSION)),
    draft_service: OperationalEventDraftService = Depends(get_draft_service),
) -> EventDraftResponse:
    """Reject one pending draft. No operational_event is created."""
    try:
        updated_draft = await draft_service.reject(
            company_id=UUID(auth_context.company_id),
            file_id=file_id,
            draft_id=draft_id,
        )
        return EventDraftResponse.model_validate(updated_draft)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Reject event draft failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Draft service unavailable",
        ) from exc
