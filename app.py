"""European options workbench with 3D Greeks and portfolio hedge analysis."""

import json
from dataclasses import asdict, replace

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from derivatives_lab import (
    Market,
    Option,
    Scenario,
    crr_price,
    explain,
    greeks,
    implied_volatility,
    portfolio_greeks,
    portfolio_value,
    price,
)
from derivatives_lab.demo import PRESETS, preset

st.set_page_config(page_title="Derivatives | Risk Lab", page_icon="◈", layout="wide")
st.caption("DERIVATIVES RISK LAB  /  EUROPEAN OPTIONS  /  SYNTHETIC MARKET")
st.title("See the Greeks. Explain the exposure.")
st.markdown("Explore nonlinear risk in 3D, challenge a delta hedge and explain a portfolio's repricing.")

with st.sidebar:
    st.header("Market")
    spot = st.slider("Underlying spot (EUR)", 60.0, 140.0, 100.0, 1.0)
    vol = st.slider("Implied volatility (%)", 5.0, 80.0, 20.0, 1.0)
    rate = st.slider("Continuous rate (%)", -2.0, 10.0, 3.0, 0.25)
    dividend = st.slider("Continuous dividend yield (%)", 0.0, 8.0, 0.0, 0.25)
    st.header("Structure")
    structure = st.selectbox("Portfolio", PRESETS)
    strike = st.slider("Reference strike (EUR)", 60.0, 140.0, 100.0, 1.0)
    days = st.slider("Days to expiry", 7, 365, 90)
    contracts = st.slider("Contracts per leg", 1, 200, 50)
    st.caption(
        "European exercise · 100 shares/contract · ACT/365 time · EUR amounts. "
        "All market inputs are illustrative."
    )

market = Market(spot, vol / 100, rate / 100, dividend / 100)
positions = preset(structure, strike, days, contracts)
risk = portfolio_greeks(positions, market)
metrics = st.columns(5)
for col, label, result in zip(
    metrics,
    [
        "Signed market value",
        "Delta (shares)",
        "Gamma (shares / EUR)",
        "Vega (EUR / vol pt)",
        "Theta (EUR / day)",
    ],
    [risk.price, risk.delta, risk.gamma, risk.vega_point, risk.theta_day],
    strict=True,
):
    col.metric(label, f"{result:,.2f}")

surfaces, portfolio, pnl, validation, method = st.tabs(
    ["3D Greeks", "Portfolio & hedge", "P&L explain", "IV & validation", "Methodology"]
)

with surfaces:
    left, middle, right = st.columns(3)
    with left:
        metric = st.selectbox("Surface metric", ["Gamma", "Delta", "Vega", "Theta", "Rho", "Price"])
    with middle:
        kind = st.selectbox("Surface option type", ["call", "put"])
    with right:
        view = st.selectbox("Visualisation", ["3D surface", "Heatmap"])
    st.caption(
        "Single LONG option unit, not the signed portfolio above. Drag to rotate; scroll to zoom. "
        "Strike, volatility, rate and dividend yield follow the sidebar."
    )
    x = [strike * (0.6 + i * 0.8 / 60) for i in range(61)]
    y = [1 + (i / 44) ** 2 * 364 for i in range(45)]
    attribute, unit = {
        "Gamma": ("gamma", "Delta change / EUR"),
        "Delta": ("delta", "Shares / unit"),
        "Vega": ("vega_point", "EUR / vol point"),
        "Theta": ("theta_day", "EUR / day"),
        "Rho": ("rho_bp", "EUR / rate bp"),
        "Price": ("price", "EUR / unit"),
    }[metric]
    z = [
        [getattr(greeks(Option(strike, t / 365, kind), replace(market, spot=s)), attribute) for s in x]
        for t in y
    ]
    if view == "3D surface":
        fig = go.Figure(
            go.Surface(
                x=x,
                y=y,
                z=z,
                colorscale="Viridis",
                colorbar={"title": unit},
                contours={"z": {"show": True, "usecolormap": True, "project_z": True}},
                hovertemplate="Spot €%{x:.1f}<br>Days %{y:.1f}<br>Value %{z:.5f}<extra></extra>",
            )
        )
        fig.update_layout(
            scene={
                "xaxis_title": "Spot (EUR)",
                "yaxis_title": "Days to expiry",
                "zaxis_title": unit,
                "camera": {"eye": {"x": 1.5, "y": -1.6, "z": 1.0}},
            }
        )
    else:
        fig = go.Figure(go.Heatmap(x=x, y=y, z=z, colorscale="Viridis", colorbar={"title": unit}))
        fig.update_layout(xaxis_title="Spot (EUR)", yaxis_title="Days to expiry")
    fig.update_layout(
        title=f"{metric} landscape · {kind} · strike €{strike:g}",
        height=570,
        margin={"l": 0, "r": 0, "b": 10, "t": 45},
    )
    st.plotly_chart(fig, width="stretch")
    explanations = {
        "Gamma": "Gamma concentrates near the strike as expiry approaches. A short option reverses this "
        "surface's sign: its delta can move rapidly against the hedge.",
        "Delta": "Delta is the local sensitivity to a EUR 1 spot change. The portfolio hedge uses signed "
        "contract-scaled delta; call and put sensitivities differ.",
        "Vega": "Vega here is per ONE volatility percentage point (20% to 21%), not a 1% relative move. "
        "It measures volatility exposure that a stock delta hedge cannot remove.",
        "Theta": "Theta measures the passage of calendar time, holding other inputs fixed. "
        "It is an instantaneous rate; a whole day's exact repricing can differ near expiry.",
        "Rho": "Rho is displayed per one basis point of the continuous annual rate. "
        "The model holds dividend yield and volatility fixed.",
        "Price": "This is theoretical European option value per underlying unit. "
        "Position value also includes signed contracts and the 100-share multiplier.",
    }
    st.info(explanations[metric])
    slice_fig = go.Figure(
        go.Scatter(
            x=x,
            y=[
                getattr(greeks(Option(strike, days / 365, kind), replace(market, spot=s)), attribute)
                for s in x
            ],
            line={"color": "#37D6C0", "width": 3},
        )
    )
    slice_fig.add_vline(x=spot, line_dash="dot", line_color="#F7B955")
    slice_fig.update_layout(
        title=f"Cross-section · {days} days remaining", xaxis_title="Spot (EUR)", yaxis_title=unit, height=270
    )
    st.plotly_chart(slice_fig, width="stretch")

with portfolio:
    st.subheader("Position-level risk")
    rows = []
    for position in positions:
        g = greeks(position.option, market)
        rows.append(
            {
                "Leg": position.name,
                "Contracts": position.contracts,
                "Strike": position.option.strike,
                "Market value EUR": g.price * position.units,
                "Delta shares": g.delta * position.units,
                "Gamma / EUR": g.gamma * position.units,
                "Vega EUR / pt": g.vega_point * position.units,
                "Theta EUR / day": g.theta_day * position.units,
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    hedge = -risk.delta
    st.metric("Stock trade for initial delta neutrality", f"{hedge:+,.2f} shares")
    st.caption(
        "Fractional shares are a theoretical hedge. A positive number buys stock; a negative "
        "number shorts it. Neutrality applies locally at inception and does not remove gamma or vega."
    )
    moves = [i / 100 for i in range(-20, 21)]
    unhedged = [portfolio_value(positions, replace(market, spot=spot * (1 + m))) - risk.price for m in moves]
    hedged = [p + hedge * spot * m for p, m in zip(unhedged, moves, strict=True)]
    fig = go.Figure()
    fig.add_scatter(x=[m * 100 for m in moves], y=unhedged, name="Options only", line={"color": "#829CFF"})
    fig.add_scatter(
        x=[m * 100 for m in moves],
        y=hedged,
        name="Options + initial delta hedge",
        line={"color": "#37D6C0", "width": 3},
    )
    fig.add_hline(y=0, line_color="#50617A")
    fig.update_layout(
        title="A static delta hedge leaves nonlinear exposure",
        xaxis_title="Instantaneous spot shock (%)",
        yaxis_title="Market-value change (EUR)",
        height=400,
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Instantaneous comparison: no time/vol/rate change or execution costs. "
        "The next tab adds those shocks and one-way stock execution cost."
    )
    st.subheader("Spot × volatility stress matrix")
    shocks = list(range(-20, 21, 2))
    vshocks = list(range(-4, 11, 1))
    matrix = [
        [
            portfolio_value(
                positions, replace(market, spot=spot * (1 + s / 100), volatility=market.volatility + v / 100)
            )
            - risk.price
            for s in shocks
        ]
        for v in vshocks
    ]
    fig = go.Figure(
        go.Heatmap(
            x=shocks,
            y=vshocks,
            z=matrix,
            colorscale="RdBu",
            zmid=0,
            colorbar={"title": "EUR"},
            hovertemplate="Spot %{x}%<br>Vol %{y} pt<br>P&L €%{z:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(xaxis_title="Spot shock (%)", yaxis_title="Volatility shock (points)", height=370)
    st.plotly_chart(fig, width="stretch")

with pnl:
    st.subheader("Explain a conditional portfolio move")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        spot_shock = st.slider("Spot shock (%)", -20, 20, 5)
    with c2:
        vol_shock = st.slider("Volatility shock (points)", -4, 10, 3)
    with c3:
        elapsed = st.slider("Elapsed days", 0, min(days, 30), 1)
    with c4:
        rate_shock = st.slider("Rate shock (bp)", -100, 100, 0, 5)
    cost_bp = st.number_input("One-way stock execution cost (bp)", 0.0, 100.0, 1.0, 0.5)
    scenario = Scenario(spot_shock / 100, float(vol_shock), float(rate_shock), float(elapsed))
    report = explain(positions, market, scenario, cost_bp)
    columns = st.columns(4)
    for column, label, amount in zip(
        columns,
        ["Exact options P&L", "Greeks approximation", "Nonlinear / cross residual", "P&L with static hedge"],
        [report.exact_pnl, report.approximation, report.residual, report.hedged_pnl],
        strict=True,
    ):
        column.metric(label, f"€{amount:,.0f}")
    values = [
        report.delta_pnl,
        report.gamma_pnl,
        report.vega_pnl,
        report.theta_pnl,
        report.rho_pnl,
        report.residual,
        0,
    ]
    fig = go.Figure(
        go.Waterfall(
            x=["Delta", "Gamma", "Vega", "Theta", "Rho", "Residual", "Exact P&L"],
            y=values,
            measure=["relative"] * 6 + ["total"],
            increasing={"marker": {"color": "#37D6C0"}},
            decreasing={"marker": {"color": "#FF7B83"}},
            totals={"marker": {"color": "#829CFF"}},
        )
    )
    fig.update_layout(title="Taylor P&L explain with explicit residual", yaxis_title="EUR", height=390)
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "This residual is approximation error: higher-order and cross-Greek effects. "
        "It is not the bad-price residual in the separate P&L Control project."
    )
    st.write(
        f"Hedge: {report.hedge_shares:+,.2f} shares · stock P&L €{report.stock_pnl:,.2f} "
        f"· execution cost €{report.hedge_cost:,.2f}."
    )
    if elapsed < days:
        rolled = tuple(
            replace(p, option=replace(p.option, expiry=p.option.expiry - elapsed / 365)) for p in positions
        )
        new_delta = portfolio_greeks(rolled, scenario.apply(market)).delta + report.hedge_shares
        st.metric("Delta AFTER the shock, including unchanged stock hedge", f"{new_delta:+,.2f} shares")
    else:
        st.info("Scenario reaches expiry: prices become payoffs; endpoint Greeks are not defined here.")
    st.warning(
        "Results are market-value changes before stock dividends, financing, margin and hedge unwind. "
        "Scenarios are conditional outcomes, not forecasts or realized accounting P&L."
    )
    export = {
        "market": asdict(market),
        "positions": [asdict(p) for p in positions],
        "scenario": asdict(scenario),
        "report": asdict(report),
    }
    st.download_button(
        "Download scenario evidence (JSON)",
        json.dumps(export, indent=2),
        "derivatives-scenario.json",
        "application/json",
    )

with validation:
    st.subheader("Price cross-check & implied volatility")
    st.caption(
        "Selected surface option type and reference strike. Tree values converge approximately; "
        "they need not agree to machine precision."
    )
    option = Option(strike, days / 365, kind)
    analytic = price(option, market)
    tree = crr_price(option, market, 600)
    st.dataframe(
        pd.DataFrame(
            [
                {"Method": "Black–Scholes–Merton", "Price / unit": analytic},
                {"Method": "Independent CRR tree · 600 steps", "Price / unit": tree},
                {"Method": "Absolute difference", "Price / unit": abs(tree - analytic)},
            ]
        ),
        hide_index=True,
    )
    premium = st.number_input(
        "Observed premium per option unit",
        min_value=0.0,
        value=float(round(analytic, 6)),
        step=0.01,
        format="%.6f",
        key=f"premium-{strike}-{days}-{kind}-{spot}-{vol}-{rate}-{dividend}",
    )
    try:
        iv = implied_volatility(option, market, premium)
        st.metric("Implied volatility", f"{iv:.4%}")
        st.caption(
            "Bisection with no-arbitrage bounds and a 0.0001%–500% annual volatility search bracket. "
            "At expiry or at an arbitrage boundary the inverse is not reported."
        )
    except (ValueError, RuntimeError) as exc:
        st.error(str(exc))
    st.markdown(
        "The tests compare all analytical Greeks with finite differences, normal CDF values with "
        "SciPy, prices with tree convergence, and calls/puts with put–call parity. "
        "The core pricing package imports no external libraries."
    )

with method:
    st.markdown(r"""
### Model and conventions
European Black–Scholes–Merton options on a spot underlying with continuous dividend yield.
Annual volatility, rate and dividend yield are decimals internally. Time is ACT/365 model years.

| Display | Unit |
|---|---|
| Delta | Shares per option unit; portfolio delta includes signed contract multipliers |
| Gamma | Change in delta per EUR 1 spot increase |
| Vega | EUR per +1 volatility percentage point |
| Theta | EUR per elapsed calendar day |
| Rho | EUR per +1 basis point in the continuous annual rate |

The 3D view is a single **long** option unit; the portfolio panels aggregate signed contracts.
A short position reverses the long option's Greeks. A stock hedge offsets delta at inception;
its gamma and vega are zero, so those exposures remain.
    """)
    st.latex(
        r"\Delta V \approx \Delta\,\Delta S + \tfrac12\Gamma(\Delta S)^2"
        r"+\nu\,\Delta\sigma+\Theta\,\Delta t+\rho\,\Delta r"
    )
    st.markdown(
        "Expiry payoff is supported; Greeks at expiry are rejected. Assumptions exclude "
        "American exercise, volatility smile/skew, discrete dividends, stochastic rates/volatility, "
        "liquidity, credit and transaction-cost effects on pricing. Static-hedge P&L excludes "
        "funding, stock dividends and margin. This is a derivatives desk demonstrator, "
        "not a complete balance-sheet risk system."
    )
