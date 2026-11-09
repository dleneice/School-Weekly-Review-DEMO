"""Build a searchable fictional student support HTML report from demo CSV snapshots.

No external packages or confidential school records are required.
"""
import argparse
import csv
import html
from collections import defaultdict, Counter
from datetime import date
from pathlib import Path


def load(path):
    with path.open(newline='', encoding='utf-8-sig') as stream:
        return list(csv.DictReader(stream))


def n(row, field):
    return int(row.get(field) or 0)


def classify(row):
    if n(row, 'f_count'):
        return 'current-f'
    if n(row, 'close_to_f_count'):
        return 'close'
    if n(row, 'watch_count'):
        return 'watch'
    return 'clear'


def create_report(source_dir, output_file, week=None):
    reviews = load(source_dir / 'student_weekly_review.csv')
    follows = load(source_dir / 'student_followup.csv')
    postings = load(source_dir / 'teacher_course_posting.csv')
    if not reviews:
        raise ValueError('Student review file has no rows')
    weeks = sorted({r['week_ending'] for r in reviews})
    week = week or weeks[-1]
    if week not in weeks:
        raise ValueError(f'Week {week} not found; choices: {", ".join(weeks)}')
    by_id = defaultdict(dict)
    for row in reviews:
        by_id[row['student_id']][row['week_ending']] = row
    follows_by_key = {(r['student_id'], r['week_ending']): r for r in follows}
    posting_lookup = {(r['week_ending'], r['course_code']): r for r in postings}
    active = [(sid, by_id[sid][week]) for sid in sorted(by_id) if week in by_id[sid]]
    rank = {'current-f': 0, 'close': 1, 'watch': 2, 'clear': 3}
    active.sort(key=lambda item: (rank[classify(item[1])], item[0]))
    counts = Counter(classify(row) for _, row in active)
    e = html.escape
    cards = []
    for sid, current in active:
        band = classify(current)
        trajectory = follows_by_key.get((sid, week), {})
        checkpoints = []
        for w in weeks:
            historical = by_id[sid].get(w)
            if not historical:
                checkpoints.append(f'<div class="checkpoint"><b>{e(w[5:])}</b><span>No snapshot</span></div>')
                continue
            checkpoints.append('<div class="checkpoint">'
                f'<b>{e(w[5:])}</b><strong>{n(historical,"f_count")} F · '
                f'{n(historical,"close_to_f_count")} close · {n(historical,"watch_count")} watch</strong>'
                f'<small>Journal count: {n(historical,"journal_entries_this_week")}</small></div>')
        failing = [x.strip() for x in (current.get('failing_course_codes') or '').split('|') if x.strip()]
        # Accept either a pipe- or comma-separated list of fictional course codes.
        if len(failing) == 1 and ',' in failing[0]:
            failing = [x.strip() for x in failing[0].split(',') if x.strip()]
        courses = []
        for course in failing:
            item = posting_lookup.get((week, course))
            posting = item.get('posting_status', 'Not supplied') if item else 'Not supplied'
            courses.append('<tr><td>' + e(course) + '</td><td>' + e(posting) + '</td></tr>')
        course_table = ('<table><thead><tr><th>Course currently below 60%</th><th>Posting context</th></tr></thead>'
                        '<tbody>' + ''.join(courses) + '</tbody></table>') if courses else '<p>No current F courses in this snapshot.</p>'
        prompt = trajectory.get('followup_prompt', '')
        cards.append(f'''<article class="student" data-group="{band}">
<div class="student-top"><div><h2>{e(sid)}</h2><p>{e(current['advisory'])} · {n(current,'courses_reported')} reported course(s)</p></div>
<span class="pill {band}">{'Current F' if band=='current-f' else 'Close 60–&lt;65' if band=='close' else 'Watch 65–&lt;70' if band=='watch' else '70+ in all courses'}</span></div>
<div class="timeline">{''.join(checkpoints)}</div>
<div class="two"><section><h3>Current snapshot</h3><p><b>{n(current,'f_count')}</b> F course(s) · <b>{n(current,'close_to_f_count')}</b> close · <b>{n(current,'watch_count')}</b> watch</p>
<p>Journal entries this week: <b>{n(current,'journal_entries_this_week')}</b></p>
<p>Course(s) below 60 without a recent posting: <b>{n(current,'failing_courses_without_weekly_post')}</b></p>
<p>Review category: {e(current['review_level'])}</p></section>
<section><h3>Changes and next review</h3><p>Trajectory: <b>{e(trajectory.get('trajectory','Not supplied'))}</b></p>
<p>{e(prompt) if prompt else 'Review course context in the approved system before deciding on support.'}</p>
<p>Action / owner / next review: <span class="blank">________________________________</span></p></section></div>
<h3>Current failing courses</h3>{course_table}
</article>''')
    report_date = date.fromisoformat(week).strftime('%B %d, %Y')
    html_doc = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fictional Student Weekly Review — ''' + e(week) + '''</title><style>
:root{font-family:Arial,Helvetica,sans-serif;color:#23364a;background:#eef2f7}*{box-sizing:border-box}body{margin:0}
main{max-width:1250px;margin:auto;padding:25px}header{background:#18344f;color:white;border-radius:12px;padding:25px 30px}
header h1{margin:0 0 6px;font-size:25px}header p{margin:0;color:#dae6f0}.demo{color:#f4c870;font-weight:bold;text-transform:uppercase;font-size:12px}
.notice{color:#54677a;line-height:1.5;background:#fff;border-left:4px solid #be8b37;padding:12px;margin:14px 0}
.toolbar{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin:15px 0}.toolbar button{border:1px solid #c4d1dc;background:white;color:#18344f;border-radius:7px;padding:10px 12px;cursor:pointer}
.toolbar button[aria-pressed="true"]{background:#18344f;color:white}.toolbar input{padding:11px;border:1px solid #c4d1dc;border-radius:7px;min-width:220px;flex:1}
.student{background:white;border:1px solid #dce4eb;border-radius:10px;padding:20px;margin-bottom:15px;break-inside:avoid}
.student-top{display:flex;justify-content:space-between;gap:12px;align-items:center}.student h2{margin:0;font-size:21px}.student-top p{color:#637589;margin:6px 0}.pill{border-radius:15px;padding:7px 11px;font-size:12px;font-weight:bold;background:#e8eef4}
.pill.current-f{color:#9c3445;background:#fce7ec}.pill.close{color:#994918;background:#fff0e0}.pill.watch{color:#866113;background:#fff7d9}.pill.clear{color:#236a5f;background:#e1f5f0}
.timeline{display:flex;gap:8px;flex-wrap:wrap;margin:15px 0}.checkpoint{flex:1;min-width:150px;background:#f3f6f9;border-radius:7px;padding:10px}.checkpoint b,.checkpoint strong,.checkpoint small{display:block;margin-bottom:6px}.checkpoint small{color:#64768a}
.two{display:grid;grid-template-columns:1fr 1fr;gap:15px}.two section{border:1px solid #e2e9ef;border-radius:9px;padding:10px 15px}.student h3{font-size:14px;color:#18344f}.student p{line-height:1.45}table{border-collapse:collapse;width:100%;font-size:13px}th{text-align:left;background:#eaf0f5}th,td{padding:10px;border-bottom:1px solid #e1e8ef}.blank{color:#97a5b3}
footer{font-size:12px;color:#657589;padding:10px 0 35px}@media(max-width:700px){.two{grid-template-columns:1fr}.student-top{align-items:start}}@media print{main{padding:0}header{border-radius:0}.toolbar,.notice{display:none}.student{box-shadow:none}body{background:white}}
</style></head><body><main><header><div class="demo">Fictional data demonstration</div><h1>Student progress and support review</h1><p>Week ending ''' + e(report_date) + ' · ' + str(len(active)) + ''' fictional students · Four-week history</p></header>
<p class="notice"><b>Portfolio demonstration only.</b> This report contains fictional IDs and aggregate journal counts—not student identities, narratives, EL/IEP fields, or verified interventions. A missing journal entry or outdated posting date is a review prompt, not evidence of staff noncompliance. The analysis is not an official ninth-grade On-Track calculation.</p>
<div class="toolbar" aria-label="Student review filters"><button type="button" data-lens="all" aria-pressed="true">All (''' + str(len(active)) + ''')</button>
<button type="button" data-lens="current-f" aria-pressed="false">Current F (''' + str(counts['current-f']) + ''')</button>
<button type="button" data-lens="close" aria-pressed="false">Close 60–&lt;65 (''' + str(counts['close']) + ''')</button>
<button type="button" data-lens="watch" aria-pressed="false">Watch 65–&lt;70 (''' + str(counts['watch']) + ''')</button>
<button type="button" data-lens="clear" aria-pressed="false">70+ (''' + str(counts['clear']) + ''')</button>
<input type="search" id="search" placeholder="Search fictional ID, advisory, or course" aria-label="Search student cards"></div>
<div id="cards">''' + ''.join(cards) + '''</div><footer>Fictional, precomputed CSV snapshots. All displayed results are generated locally. No network requests.</footer></main>
<script>let active='all';function apply(){const q=document.getElementById('search').value.toLowerCase();document.querySelectorAll('.student').forEach(c=>{c.hidden=(active!=='all'&&c.dataset.group!==active)||!c.textContent.toLowerCase().includes(q)})}document.getElementById('search').addEventListener('input',apply);document.querySelectorAll('[data-lens]').forEach(b=>b.addEventListener('click',()=>{active=b.dataset.lens;document.querySelectorAll('[data-lens]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));apply()}));</script></body></html>'''
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html_doc, encoding='utf-8')
    return len(active)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, default=Path(__file__).resolve().parents[1] / 'sample_outputs')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'reports' / 'student_weekly_review_demo.html')
    parser.add_argument('--week', help='Snapshot date YYYY-MM-DD; default latest')
    args = parser.parse_args()
    count = create_report(args.input_dir, args.output, args.week)
    print(f'Created {args.output} for {count} fictional students')
