"""Run the fictional weekly operator workflow end-to-end."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
for command in ([sys.executable,'generate_demo.py'],[sys.executable,'weekly_monitor_demo.py'],[sys.executable,'scripts/render_student_review.py']):
    subprocess.run(command,cwd=ROOT,check=True)
print('Open reports/student_weekly_review_demo.html in your browser. Sample PDF is a static reference.')
