from django.db import models


class Student(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=100)
    student_set = models.ManyToManyField(
        to=Student,
        related_name="subject_set",
        related_query_name="subject",
        through="Enrollment", # ManyToManyField 관계에서 연결 테이블을 명시하는 데 사용
        through_fields=("subject", "student"), # Enrollment 모델에서 subject와 student 필드가 Subject와 Student 모델과 연결된 필드임을 명시하는 설정
        blank=True, # 이 필드가 빈 값으로 저장될 수 있다.
    )

    def __str__(self): # 객체의 문자열 표현을 정의
        return self.name


class Enrollment(models.Model):
    class Term(models.TextChoices): # 이 내부 클래스를 사용하여 학기를 선택할 수 있는 열거형을 정의
        SPRING = "SP", "봄학기"
        SUMMER = "SU", "여름학기"
        FALL = "FA", "가을학기"
        WINTER = "WI", "겨울학기"

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE, # 해당 학생이 삭제되면 관련된 수강 정보도 삭제
        related_name="enrollment_set", #  related_name 필드를 통해 학생 모델에서 이 수강 정보에 접근할 수 있는 이름을 설정
        related_query_name="enrollment",  # 쿼리셋에서 이 관계를 참조할 때 사용할 이름을 설정
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="enrollment_set",
        related_query_name="enrollment",
    )
    year = models.PositiveIntegerField(verbose_name="수강년도")
    term = models.CharField(max_length=2, choices=Term.choices, verbose_name="학기")
    is_pass = models.BooleanField(verbose_name="이수 여부", default=False)

    class Meta:
        constraints = [ # 데이터의 무결성을 유지하기 위한 제약 조건
            models.UniqueConstraint( # 이 제약 조건은 특정 학생이 특정 과목을 특정 학년도와 학기에서 중복 수강할 수 없도록 합니다.
                fields=["student", "subject", "year", "term"], # 중복을 검사할 필드 목록을 지정
                name="school_enrollment_unique", # 제약 조건의 이름을 정의
            )
        ]
