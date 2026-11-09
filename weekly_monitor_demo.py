"""Rebuild fictional weekly support-review CSVs. Standard library only."""
import csv
from collections import defaultdict, Counter
from datetime import date, timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'
OUT=ROOT/'sample_outputs'

def read(name):
    with (DATA/name).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(name, fields, rows):
    OUT.mkdir(exist_ok=True)
    with (OUT/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    students=read('students.csv'); grades=read('grades.csv'); postings=read('teacher_postings.csv'); journals=read('journal_activity.csv')
    student_map={s['student_id']:s['advisory'] for s in students}
    weeks=sorted({g['week_ending'] for g in grades})
    if len(students)!=len(student_map) or not weeks:raise ValueError('Missing or duplicate fictional students/weeks')
    group=defaultdict(list); section=defaultdict(list); teacher_week=defaultdict(list)
    for g in grades:
        key=(g['week_ending'],g['student_id']);grp=group[key];
        if any(r['course_code']==g['course_code'] for r in grp): raise ValueError('Duplicate student-course-week record')
        if g['student_id'] not in student_map or not 0<=float(g['numeric_average'])<=100:raise ValueError('Invalid grade record')
        grp.append(g);section[(g['week_ending'],g['course_code'])].append(g);teacher_week[(g['week_ending'],g['teacher_id'])].append(g)
    posting_by={(r['week_ending'],r['course_code']):r for r in postings}
    journal_by={(r['week_ending'],r['student_id']):int(r['entry_count']) for r in journals}
    if len(posting_by)!=len(postings) or len(journal_by)!=len(journals):raise ValueError('Duplicate posting/journal key')
    post_rows=[]
    for r in postings:
        w=date.fromisoformat(r['week_ending']);posted=date.fromisoformat(r['posted_on']) if r['posted_on'] else None
        status='Posted in week' if posted and 0<=(w-posted).days<=6 else 'Review update date'
        post_rows.append(dict(**r,posting_status=status))
    write('teacher_course_posting.csv',['week_ending','teacher_id','course_code','posted_on','posting_status'],post_rows)
    post_status={(r['week_ending'],r['course_code']):r['posting_status'] for r in post_rows}
    reviews=[];follows=[];summary=Counter();failure_by=[];rates=[]
    prior_student={};prior_course={};prior_rate={}
    for w in weeks:
        for sid in sorted(student_map):
            rows=group.get((w,sid),[])
            if not rows:raise ValueError(f'Missing full fictional grade snapshot {w}/{sid}')
            failing=[r for r in rows if float(r['numeric_average'])<60]
            close=sum(60<=float(r['numeric_average'])<65 for r in rows)
            watch=sum(65<=float(r['numeric_average'])<70 for r in rows)
            d=sum(60<=float(r['numeric_average'])<70 for r in rows)
            not_post=sum(post_status.get((w,r['course_code']))!='Posted in week' for r in failing)
            journals_count=journal_by.get((w,sid),0)
            level='Follow-up review' if failing and (not_post or not journals_count) else 'Current failure' if failing else 'No current failure'
            review=dict(week_ending=w,student_id=sid,advisory=student_map[sid],courses_reported=len(rows),f_count=len(failing),d_count=d,close_to_f_count=close,watch_count=watch,failing_courses_without_weekly_post=not_post,failing_course_codes='|'.join(sorted(r['course_code'] for r in failing)),journal_entries_this_week=journals_count,review_level=level)
            reviews.append(review)
            band='Current F' if failing else 'Close 60-<65' if close else 'Watch 65-<70' if watch else '70+ in all courses'
            summary[(w,student_map[sid],band)]+=1
            old=prior_student.get(sid)
            prev=old if old is not None else ''
            trajectory='Baseline snapshot' if old is None else 'New F' if failing and old==0 else 'Persistent F' if failing else 'No longer current F' if old else 'No current F'
            prompt='Review journal and course context before selecting support' if level=='Follow-up review' else 'Review current failing courses and supports' if failing else 'Routine review'
            follows.append(dict(week_ending=w,student_id=sid,advisory=student_map[sid],f_count=len(failing),previous_f_count=prev,trajectory=trajectory,journal_entries_this_week=journals_count,followup_prompt=prompt))
            prior_student[sid]=len(failing)
        for (sw,course),items in sorted(section.items()):
            if sw!=w:continue
            failure_by.append(dict(week_ending=w,teacher_id=items[0]['teacher_id'],subject=items[0]['subject'],course_code=course,students_in_course=len(items),current_failures=sum(float(x['numeric_average'])<60 for x in items)))
        for (tw,teacher),items in sorted(teacher_week.items()):
            if tw!=w:continue
            cur={(r['student_id'],r['course_code']) for r in items if float(r['numeric_average'])<60}
            prev=prior_course.get(teacher,set())
            rate=100*len(cur)/len(items)
            previous=prior_rate.get(teacher)
            courses={r['course_code'] for r in items}
            rates.append(dict(week_ending=w,teacher_id=teacher,course_sections=len(courses),student_course_enrollments=len(items),failing_enrollments=len(cur),failure_rate_pct=f'{rate:.1f}',students_taught=len({r['student_id'] for r in items}),students_with_f=len({x[0] for x in cur}),new_failures=len(cur-prev) if previous is not None else 0,persistent_failures=len(cur&prev) if previous is not None else 0,recovered_from_f=len(prev-cur) if previous is not None else 0,sections_needing_posting_review=sum(post_status.get((w,c))!='Posted in week' for c in courses),previous_failure_rate_pct=f'{previous:.1f}' if previous is not None else '',rate_change_pp=f'{rate-previous:+.1f}' if previous is not None else ''))
            prior_course[teacher]=cur;prior_rate[teacher]=rate
    outputs={'student_weekly_review.csv':reviews,'student_followup.csv':follows,'failure_by_course.csv':failure_by,'teacher_failure_rates.csv':rates,'summary_by_week_advisory.csv':[dict(week_ending=w,advisory=a,review_level=l,students=c) for (w,a,l),c in sorted(summary.items())]}
    for name,rows in outputs.items():
        if not rows:raise ValueError(f'No output rows for {name}')
        write(name,list(rows[0]),rows)
    print(f'Generated {len(reviews)} fictional student-week snapshots across {len(weeks)} weeks; 6 CSV outputs.')
if __name__=='__main__':main()
