from pydantic import BaseModel, Field
from typing import List

class TestCase(BaseModel):
    name: str = Field(description="שם הבדיקה (למשל: test_login_success)")
    description: str = Field(description="מה הבדיקה בודקת ומה הציפייה (Assertion)")
    dependencies: List[str] = Field(description="אילו פונקציות או מחלקות צריך לעשות להן Mock")

class TestPlan(BaseModel):
    file_to_test: str = Field(description="הנתיב המלא לקובץ שנבדק")
    test_framework: str = Field(description="באיזו ספרייה להשתמש (pytest/unittest)")
    test_cases: List[TestCase] = Field(description="רשימת מקרי הבדיקה המתוכננים")