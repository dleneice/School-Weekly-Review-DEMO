"""Generate fictional weekly grades, grade-posting dates, and journal counts."""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SUBJECTS = [("ENG", "English"), ("MATH", "Math"), ("SCI", "Science"),
            ("SOC", "Social Science"), ("ELECT", "Elective")]


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def generate():
    DATA.mkdir(exist_ok=True)
    rng = random.Random(7020)
    weeks = [date(2026, 9, 4) + timedelta(days=7 * i) for i in range(4)]
    students = [{"student_id": f"S{i:04d}", "advisory": f"Advisory {1 + (i - 1) % 4}"}
                for i in range(1, 73)]
    grades, postings, journals = [], [], []
    for week_index, week in enumerate(weeks):
        week_text = week.isoformat()
        for subject_index, (code, _subject) in enumerate(SUBJECTS):
            for section in range(2):
                course_code = f"{code}1-{'A' if section == 0 else 'B'}"
                teacher_id = f"T{1 + subject_index * 2 + section:02d}"
                days_ago = (subject_index * 3 + section * 2 + week_index) % 10
                # Blank means this fictional export has no posting date for the course.
                posted_on = "" if (subject_index + section + week_index) % 11 == 0 else \
                    (week - timedelta(days=days_ago)).isoformat()
                postings.append({"week_ending": week_text, "teacher_id": teacher_id,
                                 "course_code": course_code, "posted_on": posted_on})
        for student in students:
            n = int(student["student_id"][1:])
            # Metadata only: no journal narrative or staff names.
            count = 2 if (n + week_index) % 13 == 0 else 1 if (n + week_index) % 5 == 0 else 0
            journals.append({"week_ending": week_text, "student_id": student["student_id"],
                             "entry_count": count})
            for subject_index, (code, subject) in enumerate(SUBJECTS):
                section = n % 2
                course_code = f"{code}1-{'A' if section == 0 else 'B'}"
                teacher_id = f"T{1 + subject_index * 2 + section:02d}"
                score = (n * 11 + subject_index * 13 + week_index * 5 + rng.randint(0, 8)) % 100
                # The fictional numeric scale preserves the original A-F mix.
                if score < 7:
                    average = 45 + 2 * score
                elif score < 18:
                    average = 60 + (score - 7) * 10 // 11
                elif score < 52:
                    average = 70 + (score - 18) * 10 // 34
                elif score < 80:
                    average = 80 + (score - 52) * 10 // 28
                else:
                    average = 90 + (score - 80) * 10 // 20
                grade = "F" if average < 60 else "D" if average < 70 else \
                    "C" if average < 80 else "B" if average < 90 else "A"
                grades.append({"week_ending": week_text, "student_id": student["student_id"],
                               "teacher_id": teacher_id, "course_code": course_code,
                               "subject": subject, "numeric_average": average,
                               "letter_grade": grade})
    write_csv(DATA / "students.csv", ["student_id", "advisory"], students)
    write_csv(DATA / "grades.csv",
              ["week_ending", "student_id", "teacher_id", "course_code", "subject",
               "numeric_average", "letter_grade"], grades)
    write_csv(DATA / "teacher_postings.csv",
              ["week_ending", "teacher_id", "course_code", "posted_on"], postings)
    write_csv(DATA / "journal_activity.csv",
              ["week_ending", "student_id", "entry_count"], journals)
    print(f"Wrote fictional records for {len(students)} students, 10 course sections, and {len(weeks)} weeks")


if __name__ == "__main__":
    generate()
