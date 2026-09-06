# Local validation

Validated on Python 3.12.14, macOS ARM64.

- 79 pytest cases passed, including surface/heatmap switching, portfolio changes and the expiry boundary in Streamlit.
- 99.56% statement coverage of the analytics package (227/228 statements). This is not branch coverage or app.py coverage.
- Ruff lint and formatting passed. Strict mypy passed for all six package modules.
- Analytical Greeks were checked against finite differences across calls/puts, negative rates, dividends and short expiries.
- Prices were checked against known numerical values, put–call parity and independently implemented European CRR trees.
- Normal CDF/PDF were checked against SciPy. SciPy is not imported by the core engine.
- A source distribution and dependency-free wheel built successfully. The wheel was installed into a clean environment and its CLI ran successfully.
- Browser inspection confirmed that the interactive gamma surface renders. The README figure was generated from the same model and visually reviewed.

Default scenario: short 50 calls and 50 puts, 100-share multiplier, spot/strike 100, 90 days, 20% volatility, 3% rate and no dividend yield. Shock: spot +5%, volatility +3 points, one day elapsed.

- Exact option market-value P&L: EUR −12,208.620858.
- Greeks approximation: EUR −13,130.811647.
- Approximation residual: EUR +922.190789.
- Initial stock hedge: +493.981358 shares.
- Hedged P&L after 1bp one-way stock execution cost: EUR −9,743.653880.

All scenarios are synthetic. Hedged P&L excludes dividends, financing, margin and unwind costs. Remote GitHub Actions has not yet run; it is configured for Python 3.11, 3.12 and 3.13. The local dependency snapshot records the development environment, not a portable lockfile.
