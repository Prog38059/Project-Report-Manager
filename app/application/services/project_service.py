"""Project application service."""

import calendar
from datetime import date
from typing import List, Optional
import uuid

from app.application.dtos.project_dto import (
    CreateProjectDTO,
    UpdateProjectDTO,
    ProjectResponseDTO,
)
from app.common.exceptions import DuplicateEntityError, EntityNotFoundError
from app.common.types import (
    ProjectStatusCode,
    ScenarioTypeCode,
    PeriodRole,
    PeriodGranularity,
    PeriodType,
)
from app.domain.entities.project import Project, ProjectScenario, ProjectPeriod
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.repositories.entity_repository import EntityRepository
from app.infrastructure.repositories.project_repository import ProjectRepository


class ProjectService:
    """Orchestrates Project, Scenario, and Period creation and management."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    @staticmethod
    def _to_dto(project: Project) -> ProjectResponseDTO:
        return ProjectResponseDTO(
            id=project.id,
            entity_id=project.entity_id,
            project_code=project.project_code,
            project_name=project.project_name,
            industry_code=project.industry_code,
            business_model_code=project.business_model_code,
            project_nature_code=project.project_nature_code,
            location_address=project.location_address,
            district=project.district,
            state=project.state,
            pin_code=project.pin_code,
            project_description=project.project_description,
            implementation_start=project.implementation_start,
            commercial_operation_date=project.commercial_operation_date,
            financial_year_start_month=project.financial_year_start_month,
            currency_code=project.currency_code,
            projection_granularity=project.projection_granularity,
            projection_year_count=project.projection_year_count,
            projection_start_financial_year=project.projection_start_financial_year,
            historical_data_enabled=project.historical_data_enabled,
            historical_year_count=project.historical_year_count,
            statement_layout_code=project.statement_layout_code,
            status_code=project.status_code,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    def create_project(self, dto: CreateProjectDTO) -> ProjectResponseDTO:
        with self.db_manager.session_scope() as session:
            entity_repo = EntityRepository(session)
            if not entity_repo.get_by_id(dto.entity_id):
                raise EntityNotFoundError(f"Parent entity '{dto.entity_id}' does not exist.")

            repo = ProjectRepository(session)
            if repo.get_by_code(dto.project_code):
                raise DuplicateEntityError(f"Project code '{dto.project_code}' already exists.")

            project = Project(
                entity_id=dto.entity_id,
                project_code=dto.project_code.strip(),
                project_name=dto.project_name.strip(),
                industry_code=dto.industry_code,
                business_model_code=dto.business_model_code,
                project_nature_code=dto.project_nature_code,
                location_address=dto.location_address,
                district=dto.district,
                state=dto.state,
                pin_code=dto.pin_code,
                project_description=dto.project_description,
                implementation_start=dto.implementation_start,
                commercial_operation_date=dto.commercial_operation_date,
                financial_year_start_month=dto.financial_year_start_month,
                projection_granularity=dto.projection_granularity,
                projection_year_count=dto.projection_year_count,
                projection_start_financial_year=dto.projection_start_financial_year,
                historical_data_enabled=dto.historical_data_enabled,
            )
            project.validate()
            saved_project = repo.save(project)

            # 1. Automatically generate default Base Scenario
            base_scenario = ProjectScenario(
                project_id=saved_project.id,
                scenario_code="BASE",
                scenario_name="Base Case",
                scenario_type=ScenarioTypeCode.BASE,
                is_default=True,
            )
            repo.save_scenario(base_scenario)

            # 2. Automatically generate projection periods (7 years by default per ADR-002)
            periods: List[ProjectPeriod] = []
            start_month = saved_project.financial_year_start_month
            start_year = saved_project.projection_start_financial_year

            for seq in range(1, saved_project.projection_year_count + 1):
                p_start_year = start_year + seq - 1
                if start_month == 1:
                    p_end_year = p_start_year
                    p_end_month = 12
                    fy_label = f"FY {p_start_year}"
                else:
                    p_end_year = p_start_year + 1
                    p_end_month = start_month - 1
                    fy_label = f"FY {p_start_year}-{str(p_end_year)[-2:]}"

                last_day = calendar.monthrange(p_end_year, p_end_month)[1]
                period = ProjectPeriod(
                    project_id=saved_project.id,
                    period_sequence=seq,
                    period_role=PeriodRole.PROJECTION,
                    period_granularity=PeriodGranularity.ANNUAL,
                    period_label=f"Project Year {seq}",
                    period_type=PeriodType.FULL_YEAR,
                    start_date=date(p_start_year, start_month, 1),
                    end_date=date(p_end_year, p_end_month, last_day),
                    financial_year_label=fy_label,
                    display_sequence=seq,
                    is_report_column=True,
                )
                periods.append(period)

            repo.save_periods(periods)
            return self._to_dto(saved_project)

    def update_project(self, project_id: uuid.UUID, dto: UpdateProjectDTO) -> ProjectResponseDTO:
        with self.db_manager.session_scope() as session:
            repo = ProjectRepository(session)
            project = repo.get_by_id(project_id)
            if not project:
                raise EntityNotFoundError(f"Project '{project_id}' not found.")

            if dto.project_name is not None:
                project.project_name = dto.project_name.strip()
            if dto.industry_code is not None:
                project.industry_code = dto.industry_code
            if dto.business_model_code is not None:
                project.business_model_code = dto.business_model_code
            if dto.project_nature_code is not None:
                project.project_nature_code = dto.project_nature_code
            if dto.location_address is not None:
                project.location_address = dto.location_address
            if dto.district is not None:
                project.district = dto.district
            if dto.state is not None:
                project.state = dto.state
            if dto.pin_code is not None:
                project.pin_code = dto.pin_code
            if dto.project_description is not None:
                project.project_description = dto.project_description
            if dto.implementation_start is not None:
                project.implementation_start = dto.implementation_start
            if dto.commercial_operation_date is not None:
                project.commercial_operation_date = dto.commercial_operation_date
            if dto.status_code is not None:
                project.status_code = dto.status_code
            if dto.historical_data_enabled is not None:
                project.historical_data_enabled = dto.historical_data_enabled

            project.validate()
            saved = repo.save(project)
            return self._to_dto(saved)

    def get_project(self, project_id: uuid.UUID) -> Optional[ProjectResponseDTO]:
        with self.db_manager.session_scope() as session:
            repo = ProjectRepository(session)
            project = repo.get_by_id(project_id)
            return self._to_dto(project) if project else None

    def list_projects_for_entity(self, entity_id: uuid.UUID) -> List[ProjectResponseDTO]:
        with self.db_manager.session_scope() as session:
            repo = ProjectRepository(session)
            projects = repo.list_by_entity_id(entity_id)
            return [self._to_dto(p) for p in projects]

    def list_all_projects(self, include_archived: bool = False) -> List[ProjectResponseDTO]:
        with self.db_manager.session_scope() as session:
            repo = ProjectRepository(session)
            projects = repo.list_all(include_archived=include_archived)
            return [self._to_dto(p) for p in projects]

    def archive_project(self, project_id: uuid.UUID) -> None:
        with self.db_manager.session_scope() as session:
            repo = ProjectRepository(session)
            project = repo.get_by_id(project_id)
            if not project:
                raise EntityNotFoundError(f"Project '{project_id}' not found.")
            repo.archive(project_id)

    def list_periods(self, project_id: uuid.UUID) -> List[ProjectPeriod]:
        with self.db_manager.session_scope() as session:
            repo = ProjectRepository(session)
            return repo.list_periods(project_id)

    def list_scenarios(self, project_id: uuid.UUID) -> List[ProjectScenario]:
        with self.db_manager.session_scope() as session:
            repo = ProjectRepository(session)
            return repo.list_scenarios(project_id)
