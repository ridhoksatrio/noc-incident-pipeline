import sys
from datetime import timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .database import SessionLocal
from .metrics import summary
from .models import utcnow

ROOT = Path(__file__).resolve().parent.parent


def build_html(days=7):
    db = SessionLocal()
    end = utcnow()
    start = end - timedelta(days=days)
    data = summary(db, start, end)
    db.close()
    env = Environment(
        loader=FileSystemLoader(ROOT / 'templates'),
        autoescape=True,
    )
    return env.get_template('weekly.html').render(
        d=data, start=start, end=end, days=days
    )


if __name__ == '__main__':
    days = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 7
    out_dir = ROOT / 'reports'
    out_dir.mkdir(exist_ok=True)
    html = build_html(days)

    if '--html' in sys.argv:
        path = out_dir / f'report-{days}d.html'
        path.write_text(html, encoding='utf-8')
    else:
        from weasyprint import HTML
        path = out_dir / f'report-{days}d.pdf'
        HTML(string=html).write_pdf(str(path))

    print('Laporan dibuat:', path)