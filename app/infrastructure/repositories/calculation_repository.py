"""Repository for Financial Calculation Runs, Snapshots, and Statement Results."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.database.models.calculation_model import (
    AssetScheduleResultModel,
    CalculationRunModel,
    CalculationRunSnapshotModel,
    EntityStatementMappingModel,
    LoanScheduleResultModel,
    StatementLineDefinitionModel,
    StatementLineResultModel,
)


class CalculationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_next_run_number(self, scenario_id: uuid.UUID) -> int:
        stmt = select(func.coalesce(func.max(CalculationRunModel.run_number), 0)).where(
            CalculationRunModel.scenario_id == scenario_id
        )
        current_max = self.session.execute(stmt).scalar_one()
        return current_max + 1

    def create_calculation_run(
        self,
        project_id: uuid.UUID,
        scenario_id: uuid.UUID,
        engine_version: str,
        input_hash: str,
        run_status: str = "SUCCESS",
        prepared_by_label: Optional[str] = None,
        summary_note: Optional[str] = None,
        validation_error_count: int = 0,
        validation_warning_count: int = 0,
    ) -> CalculationRunModel:
        run_number = self.get_next_run_number(scenario_id)
        run = CalculationRunModel(
            id=uuid.uuid4(),
            project_id=project_id,
            scenario_id=scenario_id,
            run_number=run_number,
            engine_version=engine_version,
            input_hash=input_hash,
            run_timestamp=datetime.now(timezone.utc),
            run_status=run_status,
            prepared_by_label=prepared_by_label,
            summary_note=summary_note,
            validation_error_count=validation_error_count,
            validation_warning_count=validation_warning_count,
        )
        self.session.add(run)
        self.session.flush()
        return run

    def save_snapshot(
        self,
        calculation_run_id: uuid.UUID,
        input_snapshot_json: str,
        input_hash: str,
        snapshot_schema_version: str = "1.0",
    ) -> CalculationRunSnapshotModel:
        snapshot = CalculationRunSnapshotModel(
            id=uuid.uuid4(),
            calculation_run_id=calculation_run_id,
            snapshot_schema_version=snapshot_schema_version,
            input_snapshot_json=input_snapshot_json,
            input_hash=input_hash,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(snapshot)
        self.session.flush()
        return snapshot

    def save_statement_results(
        self,
        statement_results: List[StatementLineResultModel],
    ) -> None:
        self.session.add_all(statement_results)
        self.session.flush()

    def save_loan_results(
        self,
        loan_results: List[LoanScheduleResultModel],
    ) -> None:
        self.session.add_all(loan_results)
        self.session.flush()

    def save_asset_results(
        self,
        asset_results: List[AssetScheduleResultModel],
    ) -> None:
        self.session.add_all(asset_results)
        self.session.flush()

    def get_latest_run(self, scenario_id: uuid.UUID) -> Optional[CalculationRunModel]:
        stmt = (
            select(CalculationRunModel)
            .where(CalculationRunModel.scenario_id == scenario_id)
            .order_by(CalculationRunModel.run_number.desc())
            .limit(1)
        )
        return self.session.execute(stmt).scalars().first()

    def get_run_by_id(self, run_id: uuid.UUID) -> Optional[CalculationRunModel]:
        return self.session.get(CalculationRunModel, run_id)

    def list_runs_for_scenario(self, scenario_id: uuid.UUID) -> List[CalculationRunModel]:
        stmt = (
            select(CalculationRunModel)
            .where(CalculationRunModel.scenario_id == scenario_id)
            .order_by(CalculationRunModel.run_number.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_statement_lines_for_run(
        self,
        run_id: uuid.UUID,
        statement_type: Optional[str] = None,
    ) -> List[StatementLineResultModel]:
        stmt = select(StatementLineResultModel).where(
            StatementLineResultModel.calculation_run_id == run_id
        )
        if statement_type:
            stmt = stmt.where(StatementLineResultModel.statement_type == statement_type)
        return list(self.session.execute(stmt).scalars().all())

    def get_loan_schedules_for_run(
        self,
        run_id: uuid.UUID,
    ) -> List[LoanScheduleResultModel]:
        stmt = (
            select(LoanScheduleResultModel)
            .where(LoanScheduleResultModel.calculation_run_id == run_id)
            .order_by(LoanScheduleResultModel.installment_number)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_asset_schedules_for_run(
        self,
        run_id: uuid.UUID,
    ) -> List[AssetScheduleResultModel]:
        stmt = (
            select(AssetScheduleResultModel)
            .where(AssetScheduleResultModel.calculation_run_id == run_id)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_statement_line_definitions(self, active_only: bool = True) -> List[StatementLineDefinitionModel]:
        stmt = select(StatementLineDefinitionModel)
        if active_only:
            stmt = stmt.where(StatementLineDefinitionModel.active_flag.is_(True))
        stmt = stmt.order_by(StatementLineDefinitionModel.sort_order)
        return list(self.session.execute(stmt).scalars().all())
