"""Exercise the actual dashboard controls and expiry boundary."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard():
    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py")).run(timeout=30)
    assert not app.exception
    assert "-" in app.metric[2].value
    next(w for w in app.selectbox if w.label == "Surface metric").select("Vega").run(timeout=30)
    assert not app.exception
    next(w for w in app.selectbox if w.label == "Visualisation").select("Heatmap").run(timeout=30)
    assert not app.exception
    next(w for w in app.selectbox if w.label == "Portfolio").select("Long call").run(timeout=30)
    assert not app.exception
    assert "-" not in app.metric[2].value
    next(w for w in app.slider if w.label == "Days to expiry").set_value(7).run(timeout=30)
    next(w for w in app.slider if w.label == "Elapsed days").set_value(7).run(timeout=30)
    assert not app.exception
    assert any("reaches expiry" in info.value for info in app.info)
