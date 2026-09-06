"""Regenerate the README figure and standalone interactive gamma chart.

Install extras: pip install -e '.[app,docs]'
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import plotly.graph_objects as go  # noqa: E402

from derivatives_lab import Market, Option, greeks  # noqa: E402

root = Path(__file__).resolve().parents[1] / "docs"
x = [60 + i * 80 / 60 for i in range(61)]
y = [1 + (i / 44) ** 2 * 364 for i in range(45)]
z = [[greeks(Option(100, t / 365), Market(spot=s)).gamma for s in x] for t in y]
fig = go.Figure(go.Surface(x=x, y=y, z=z, colorscale="Viridis", colorbar={"title": "Gamma"}))
fig.update_layout(
    title="Gamma landscape · long European call · strike EUR 100 · volatility 20%",
    template="plotly_dark",
    paper_bgcolor="#0B1120",
    scene={"xaxis_title": "Spot (EUR)", "yaxis_title": "Days to expiry", "zaxis_title": "Gamma / EUR"},
    margin={"l": 0, "r": 0, "t": 55, "b": 0},
)
fig.write_html(
    root / "gamma-surface.html",
    include_plotlyjs=True,
    full_html=True,
    config={"displaylogo": False, "responsive": True},
)
plt.style.use("dark_background")
preview = plt.figure(figsize=(12, 6.4), facecolor="#0B1120")
axis = preview.add_subplot(111, projection="3d", facecolor="#0B1120")
x_grid, y_grid = np.meshgrid(x, y)
axis.plot_surface(x_grid, y_grid, np.array(z), cmap="viridis", linewidth=0, antialiased=True)
axis.view_init(elev=25, azim=-60)
axis.set_xlabel("Spot (EUR)", labelpad=12)
axis.set_ylabel("Days to expiry", labelpad=12)
axis.set_zlabel("Gamma / EUR", labelpad=10)
axis.xaxis.pane.fill = axis.yaxis.pane.fill = axis.zaxis.pane.fill = False
preview.suptitle("DERIVATIVES RISK LAB  |  Gamma landscape", fontsize=20, x=0.5, y=0.96)
preview.text(
    0.5,
    0.89,
    "One long European call · strike EUR 100 · volatility 20% · synthetic model",
    ha="center",
    fontsize=11,
    color="#A2AEC2",
)
preview.text(
    0.5,
    0.04,
    "A delta hedge removes the local slope. Nonlinear exposure remains.",
    ha="center",
    fontsize=12,
    color="#37D6C0",
)
preview.savefig(root / "preview.png", dpi=150, facecolor=preview.get_facecolor(), bbox_inches="tight")
plt.close(preview)
