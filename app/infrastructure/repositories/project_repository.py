"""Project persistence repository."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.types import (
    ProjectNatureCode,
    ProjectStatusCode,
    ScenarioTypeCode,
    PeriodRole,
    PeriodGranularity,
    PeriodType,
)
from app.domain.entities.project import Project, ProjectScenario, ProjectPeriod
from app.infrastructure.database.models.project_model import (
    ProjectModel,
    ProjectScenarioModel,
    ProjectPeriodModel,
)


class ProjectRepository:
    """Repository handling Project, Scenario, and Period persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _to_entity(model: ProjectModel) -> Project:
        return Project(
            id=model.id,
            entity_id=model.entity_id,
            project_code=model.project_code,
            project_name=model.project_name,
            industry_code=model.industry_code,
            business_model_code=model.business_model_code,
            project_nature_code=ProjectNatureCode(model.project_nature_code),
            location_address=model.location_address,
            district=model.district,
            state=model.state,
            pin_code=model.pin_code,
            project_description=model.project_description,
            implementation_start=model.implementation_start,
            commercial_operation_date=model.commercial_operation_date,
            financial_year_start_month=model.financial_year_start_month,
            currency_code=model.currency_code,
            projection_granularity=PeriodGranularity(model.projection_granularity),
            projection_year_count=model.projection_year_count,
            projection_start_financial_year=model.projection_start_financial_year,
            historical_data_enabled=model.historical_data_enabled,
            historical_year_count=model.historical_year_count,
            statement_layout_code=model.statement_layout_code,
            status_code=ProjectStatusCode(model.status_code),
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by_label=model.created_by_label,
            updated_by_label=model.updated_by_label,
        )

    def get_by_id(self, project_id: uuid.UUID) -> Optional[Project]:
        model = self.session.get(ProjectModel, project_id)
        return self._to_entity(model) if model else None

    def get_by_code(self, project_code: str) -> Optional[Project]:
        stmt = select(ProjectModel).where(ProjectModel.project_code == project_code.strip())
        model = self.session.execute(stmt).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def list_by_entity_id(self, entity_id: uuid.UUID, include_archived: bool = False) -> List[Project]:
        stmt = select(ProjectModel).where(ProjectModel.entity_id == entity_id)
        if not include_archived:
            stmt = stmt.where(ProjectModel.status_code != ProjectStatusCode.ARCHIVED.value)
        stmt = stmt.order_by(ProjectModel.project_name)
        models = self.session.execute(stmt).scalars().all()
        return [self._to_entity(m) for m in models]

    def list_all(self, include_archived: bool = False) -> List[Project]:
        stmt = select(ProjectModel)
        if not include_archived:
            stmt = stmt.where(ProjectModel.status_code != ProjectStatusCode.ARCHIVED.value)
        stmt = stmt.order_by(ProjectModel.created_at.desc())
        models = self.session.execute(stmt).scalars().all()
        return [self._to_entity(m) for m in models]

    def save(self, project: Project) -> Project:
        model = self.session.get(ProjectModel, project.id)
        now = datetime.now(timezone.utc)
        nature_str = project.project_nature_code.value if hasattr(project.project_nature_code, "value") else str(project.project_nature_code)
        status_str = project.status_code.value if hasattr(project.status_code, "value") else str(project.status_code)
        granularity_str = project.projection_granularity.value if hasattr(project.projection_granularity, "value") else str(project.projection_granularity)

        if model is None:
            model = ProjectModel(
                id=project.id,
                entity_id=project.entity_id,
                project_code=project.project_code,
                project_name=project.project_name,
                industry_code=project.industry_code,
                business_model_code=project.business_model_code,
                project_nature_code=nature_str,
                location_address=project.location_address,
                district=project.district,
                state=project.state,
                pin_code=project.pin_code,
                project_description=project.project_description,
                implementation_start=project.implementation_start,
                commercial_operation_date=project.commercial_operation_date,
                financial_year_start_month=project.financial_year_start_month,
                currency_code=project.currency_code,
                projection_granularity=granularity_str,
                projection_year_count=project.projection_year_count,
                projection_start_financial_year=project.projection_start_financial_year,
                historical_data_enabled=project.historical_data_enabled,
                historical_year_count=project.historical_year_count,
                statement_layout_code=project.statement_layout_code,
                status_code=status_str,
                created_at=project.created_at or now,
                updated_at=now,
                created_by_label=project.created_by_label,
                updated_by_label=project.updated_by_label,
            )
            self.session.add(model)
        else:
            model.project_code = project.project_code
            model.project_name = project.project_name
            model.industry_code = project.industry_code
            model.business_model_code = project.business_model_code
            model.project_nature_code = nature_str
            model.location_address = project.location_address
            model.district = project.district
            model.state = project.state
            model.pin_code = project.pin_code
            model.project_description = project.project_description
            model.implementation_start = project.implementation_start
            model.commercial_operation_date = project.commercial_operation_date
            model.financial_year_start_month = project.financial_year_start_month
            model.currency_code = project.currency_code
            model.projection_granularity = granularity_str
            model.projection_year_count = project.projection_year_count
            model.projection_start_financial_year = project.projection_start_financial_year
            model.historical_data_enabled = project.historical_data_enabled
            model.historical_year_count = project.historical_year_count
            model.statement_layout_code = project.statement_layout_code
            model.status_code = status_str
            model.updated_at = now
            model.updated_by_label = project.updated_by_label

        self.session.flush()
        return self._to_entity(model)

    def archive(self, project_id: uuid.UUID) -> None:
        model = self.session.get(ProjectModel, project_id)
        if model:
            model.status_code = ProjectStatusCode.ARCHIVED.value
            model.is_active = False
            model.updated_at = datetime.now(timezone.utc)
            self.session.flush()

    # Scenario operations
    @staticmethod
    def _scenario_to_entity(m: ProjectScenarioModel) -> ProjectScenario:
        return ProjectScenario(
            id=m.id,
            project_id=m.project_id,
            scenario_code=m.scenario_code,
            scenario_name=m.scenario_name,
            scenario_type=ScenarioTypeCode(m.scenario_type),
            parent_scenario_id=m.parent_scenario_id,
            probability_pct=m.probability_pct,
            is_default=m.is_default,
            notes=m.notes,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def list_scenarios(self, project_id: uuid.UUID) -> List[ProjectScenario]:
        stmt = select(ProjectScenarioModel).where(
            ProjectScenarioModel.project_id == project_id,
            ProjectScenarioModel.is_active.is_(True),
        )
        models = self.session.execute(stmt).scalars().all()
        return [self._scenario_to_entity(m) for m in models]

    def save_scenario(self, scenario: ProjectScenario) -> ProjectScenario:
        m = self.session.get(ProjectScenarioModel, scenario.id)
        now = datetime.now(timezone.utc)
        type_str = scenario.scenario_type.value if hasattr(scenario.scenario_type, "value") else str(scenario.scenario_type)
        if m is None:
            m = ProjectScenarioModel(
                id=scenario.id,
                project_id=scenario.project_id,
                scenario_code=scenario.scenario_code,
                scenario_name=scenario.scenario_name,
                scenario_type=type_str,
                parent_scenario_id=scenario.parent_scenario_id,
                probability_pct=scenario.probability_pct,
                is_default=scenario.is_default,
                notes=scenario.notes,
                created_at=scenario.created_at or now,
                updated_at=now,
            )
            self.session.add(m)
        else:
            m.scenario_code = scenario.scenario_code
            m.scenario_name = scenario.scenario_name
            m.scenario_type = type_str
            m.parent_scenario_id = scenario.parent_scenario_id
            m.probability_pct = scenario.probability_pct
            m.is_default = scenario.is_default
            m.notes = scenario.notes
            m.updated_at = now

        self.session.flush()
        return self._scenario_to_entity(m)

    # Period operations
    @staticmethod
    def _period_to_entity(m: ProjectPeriodModel) -> ProjectPeriod:
        return ProjectPeriod(
            id=m.id,
            project_id=m.project_id,
            period_sequence=m.period_sequence,
            period_role=PeriodRole(m.period_role),
            period_granularity=PeriodGranularity(m.period_granularity),
            period_label=m.period_label,
            period_type=PeriodType(m.period_type),
            start_date=m.start_date,
            end_date=m.end_date,
            financial_year_label=m.financial_year_label,
            display_sequence=m.display_sequence,
            is_report_column=m.is_report_column,
        )

    def list_periods(self, project_id: uuid.UUID) -> List[ProjectPeriod]:
        stmt = (
            select(ProjectPeriodModel)
            .where(ProjectPeriodModel.project_id == project_id)
            .order_by(ProjectPeriodModel.display_sequence)
        )
        models = self.session.execute(stmt).scalars().all()
        return [self._period_to_entity(m) for m in models]

    def save_periods(self, periods: List[ProjectPeriod]) -> None:
        for p in periods:
            m = self.session.get(ProjectPeriodModel, p.id)
            role_str = p.period_role.value if hasattr(p.period_role, "value") else str(p.period_role)
            gran_str = p.period_granularity.value if hasattr(p.period_granularity, "value") else str(p.period_granularity)
            type_str = p.period_type.value if hasattr(p.period_type, "value") else str(p.period_type)

            if m is None:
                m = ProjectPeriodModel(
                    id=p.id,
                    project_id=p.project_id,
                    period_sequence=p.period_sequence,
                    period_role=role_str,
                    period_granularity=gran_str,
                    period_label=p.period_label,
                    period_type=type_str,
                    start_date=p.start_date,
                    end_date=p.end_date,
                    financial_year_label=p.financial_year_label,
                    display_sequence=p.display_sequence,
                    is_report_column=p.is_report_column,
                )
                self.session.add(m)
            else:
                m.period_sequence = p.period_sequence
                m.period_role = role_str
                m.period_granularity = gran_str
                m.period_label = p.period_label
                m.period_type = type_str
                m.start_date = p.start_date
                m.end_date = p.end_date
                m.financial_year_label = p.financial_year_label
                m.display_sequence = p.display_sequence
                m.is_report_column = p.is_report_column
        self.session.flush()
