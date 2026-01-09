from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload
from app.models.user import User, UserRole, UserGrade, UserStatus
from app.models.classroom import ClassModel
from app.models.promotion_history import PromotionHistory, PromotionStatus
from app.schemas.promotion import StudentPromotionDetail, PromotionPreviewResponse
import json
import logging

logger = logging.getLogger(__name__)

class PromotionService:
    
    GRADE_PROGRESSION = {
        UserGrade.TKA: UserGrade.TKB,
        UserGrade.TKB: UserGrade.SD1,
        UserGrade.SD1: UserGrade.SD2,
        UserGrade.SD2: UserGrade.SD3,
        UserGrade.SD3: UserGrade.SD4,
        UserGrade.SD4: UserGrade.SD5,
        UserGrade.SD5: UserGrade.SD6,
        UserGrade.SD6: UserGrade.SMP1,
        UserGrade.SMP1: UserGrade.SMP2,
        UserGrade.SMP2: UserGrade.SMP3,
        UserGrade.SMP3: None  # Graduated
    }

    @staticmethod
    async def get_classes_by_grade(db: AsyncSession) -> Dict[str, List[ClassModel]]:
        """
        Fetch all classes and group them by grade.
        Assumes class name starts with the grade (e.g., "SD1 A").
        Returns a dict: {"SD1": [ClassModel, ...], ...}
        """
        result = await db.execute(select(ClassModel))
        classes = result.scalars().all()
        
        classes_by_grade = {}
        for cls in classes:
            # Infer grade from class name
            # We check if the class name starts with any of the known grades
            found_grade = None
            for grade in UserGrade:
                if cls.name.upper().startswith(grade.value):
                    found_grade = grade.value
                    break
            
            if found_grade:
                if found_grade not in classes_by_grade:
                    classes_by_grade[found_grade] = []
                classes_by_grade[found_grade].append(cls)
        
        return classes_by_grade

    @staticmethod
    async def preview_promotion(db: AsyncSession, exclude_student_ids: List[int]) -> PromotionPreviewResponse:
        # 1. Fetch all active students
        query = select(User).options(joinedload(User.class_obj)).where(
            User.role == UserRole.student,
            User.status == UserStatus.active
        )
        if exclude_student_ids:
            query = query.where(User.id.notin_(exclude_student_ids))
            
        result = await db.execute(query)
        students = result.scalars().all()
        
        # 2. Fetch all classes grouped by grade
        classes_by_grade = await PromotionService.get_classes_by_grade(db)
        
        details = []
        summary = {"promoted": 0, "graduated": 0, "no_class_available": 0, "error": 0}
        
        # Helper to distribute students evenly
        # We'll keep track of assigned counts for each class to balance them
        # But for a preview, we can just do round-robin based on the list index or something deterministic
        # To be deterministic and balanced, we can sort students by ID and distribute.
        
        # Group students by next grade and region to distribute them
        students_by_group = {}
        
        for student in students:
            if not student.grade:
                # Skip students without a grade
                continue
                
            current_grade = student.grade
            next_grade = PromotionService.GRADE_PROGRESSION.get(current_grade)
            
            if next_grade is None:
                # Graduated
                details.append(StudentPromotionDetail(
                    student_id=student.id,
                    student_name=student.name,
                    old_grade=current_grade,
                    old_class_id=student.class_id,
                    old_class_name=student.class_obj.name if student.class_obj else None,
                    new_grade=None,
                    new_class_id=None,
                    new_class_name=None,
                    status="graduated"
                ))
                summary["graduated"] += 1
            else:
                # Group by (next_grade, region_id)
                group_key = (next_grade, student.region_id)
                if group_key not in students_by_group:
                    students_by_group[group_key] = []
                students_by_group[group_key].append(student)

        # Process promotions
        for (next_grade, region_id), student_list in students_by_group.items():
            all_grade_classes = classes_by_grade.get(next_grade, [])
            
            # Filter classes by region
            available_classes = [c for c in all_grade_classes if c.region_id == region_id]
            
            if not available_classes:
                # No classes available for this grade in this region
                for student in student_list:
                    details.append(StudentPromotionDetail(
                        student_id=student.id,
                        student_name=student.name,
                        old_grade=student.grade,
                        old_class_id=student.class_id,
                        old_class_name=student.class_obj.name if student.class_obj else None,
                        new_grade=next_grade,
                        new_class_id=None,
                        new_class_name=None,
                        status="no_class_available"
                    ))
                    summary["no_class_available"] += 1
                continue
            
            # Sort classes by ID for deterministic assignment
            available_classes.sort(key=lambda c: c.id)
            
            # Sort students by ID
            student_list.sort(key=lambda s: s.id)
            
            # Distribute
            for i, student in enumerate(student_list):
                target_class = available_classes[i % len(available_classes)]
                
                details.append(StudentPromotionDetail(
                    student_id=student.id,
                    student_name=student.name,
                    old_grade=student.grade,
                    old_class_id=student.class_id,
                    old_class_name=student.class_obj.name if student.class_obj else None,
                    new_grade=next_grade,
                    new_class_id=target_class.id,
                    new_class_name=target_class.name,
                    status="promoted"
                ))
                summary["promoted"] += 1
                
        return PromotionPreviewResponse(summary=summary, details=details)

    @staticmethod
    async def confirm_promotion(db: AsyncSession, exclude_student_ids: List[int]) -> PromotionHistory:
        # 1. Get the plan
        preview = await PromotionService.preview_promotion(db, exclude_student_ids)
        
        # 2. Filter only actionable items (promoted or graduated)
        actionable_details = [
            d for d in preview.details 
            if d.status in ["promoted", "graduated"]
        ]
        
        if not actionable_details:
            return None
            
        # 3. Create history record
        history_details = [d.model_dump() for d in actionable_details]
        history = PromotionHistory(
            details=history_details,
            status=PromotionStatus.applied
        )
        db.add(history)
        await db.flush() # Get ID
        
        # 4. Apply changes
        for detail in actionable_details:
            stmt = update(User).where(User.id == detail.student_id).values(
                grade=detail.new_grade,
                class_id=detail.new_class_id
            )
            await db.execute(stmt)
            
        await db.commit()
        await db.refresh(history)
        return history

    @staticmethod
    async def get_promotion_history(db: AsyncSession) -> List[PromotionHistory]:
        """Get all promotion history records, newest first."""
        result = await db.execute(
            select(PromotionHistory).order_by(PromotionHistory.promotion_date.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_promotion_history_by_id(db: AsyncSession, history_id: int) -> Optional[PromotionHistory]:
        """Get a specific promotion history record by ID."""
        result = await db.execute(
            select(PromotionHistory).where(PromotionHistory.id == history_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def undo_promotion(db: AsyncSession, history_id: int) -> bool:
        # 1. Fetch history
        result = await db.execute(select(PromotionHistory).where(PromotionHistory.id == history_id))
        history = result.scalar_one_or_none()
        
        if not history or history.status != PromotionStatus.applied:
            return False
            
        # 2. Revert changes
        details = history.details
        for detail in details:
            # detail is a dict here because it's from JSON column
            stmt = update(User).where(User.id == detail['student_id']).values(
                grade=detail['old_grade'],
                class_id=detail['old_class_id']
            )
            await db.execute(stmt)
            
        # 3. Update history status
        history.status = PromotionStatus.reverted
        await db.commit()
        return True
