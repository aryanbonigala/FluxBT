from __future__ import annotations

import os
from datetime import datetime
import pandas as pd

from .plotting import plot_drawdown, plot_equity_curve


def generate_html_report(
    params: dict[str, object],
    metrics: dict[str, float],
    equity: pd.Series,
    out_dir: str | None = None,
) -> str | None:
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except Exception:
        print("jinja2 not installed; skipping HTML report generation.")
        return None

    ts_dir = out_dir or os.path.join("runs", datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(ts_dir, exist_ok=True)

    eq_path = os.path.join(ts_dir, "equity.png")
    dd_path = os.path.join(ts_dir, "drawdown.png")
    plot_equity_curve(equity, savepath=eq_path)
    drawdown = (equity / equity.cummax() - 1.0).fillna(0.0)
    plot_drawdown(drawdown, savepath=dd_path)

    template_str = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>quantbt Report</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 20px; }
      .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
      table { border-collapse: collapse; width: 100%; }
      th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }
      th { background: #f5f5f5; }
      .left { text-align: left; }
    </style>
  </head>
  <body>
    <h1>quantbt Report</h1>
    <h2>Parameters</h2>
    <table>
      <tr><th class="left">Key</th><th>Value</th></tr>
      {% for k, v in params.items() %}
      <tr><td class="left">{{k}}</td><td>{{v}}</td></tr>
      {% endfor %}
    </table>
    <h2>Metrics</h2>
    <table>
      <tr><th class="left">Metric</th><th>Value</th></tr>
      {% for k, v in metrics.items() %}
      <tr><td class="left">{{k}}</td><td>{{"%0.6f" % v if v==v else "nan"}}</td></tr>
      {% endfor %}
    </table>
    <div class="grid">
      <div>
        <h3>Equity Curve</h3>
        <img src="equity.png" style="width:100%" />
      </div>
      <div>
        <h3>Drawdown</h3>
        <img src="drawdown.png" style="width:100%" />
      </div>
    </div>
  </body>
</html>
"""

    env = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
    template = env.from_string(template_str)
    html = template.render(params=params, metrics=metrics)
    out_path = os.path.join(ts_dir, "report.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path
