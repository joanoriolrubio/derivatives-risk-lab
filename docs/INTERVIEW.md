# Interview demo and positioning

## What to show first for this role

Lead with **P&L Control & Explain** because the vacancy explicitly asks for daily P&L control, issue resolution and management reporting. Use **Derivatives Risk Lab** next to demonstrate options knowledge and nonlinear risk visually. Keep **Fixed Income Analytics** available for a deeper discussion of curves and valuation.

These are desk-level demonstrators. Total-balance-sheet reporting remains outside their scope; acknowledge that and explain which funding, asset/liability and behavioural data would be needed.

## Two-minute derivatives walkthrough

1. Rotate the gamma surface. It is one long option, with a ridge near the strike close to expiry.
2. Point to the negative portfolio gamma: the default position is short calls and puts, so the signed exposure reverses the long-unit surface.
3. Change to vega. Explain why trading underlying stock cannot hedge volatility exposure.
4. Open the hedge chart. Zero initial delta flattens the local slope, but the curved loss profile remains.
5. Apply +5% spot, +3 volatility points and one day. Exact option P&L is about EUR −12,209; hedged P&L is about EUR −9,744.
6. Explain the approximation residual and show the changed post-shock delta.

## Questions worth preparing

**Why do gamma and vega matter after hedging delta?** Stock contributes delta but no option gamma or vega. A local slope hedge does not remove curvature or volatility exposure.

**What does a volatility point mean?** 20% to 21% is +1 point, or +0.01 in annual decimal σ. It is not a 1% relative increase.

**Is the Greeks explanation an accounting reconciliation?** No. It approximates model-value changes. The residual is omitted nonlinear/cross effects. The separate P&L project demonstrates accounting and observed-price reconciliation.

**Why does delta neutrality disappear?** The option delta changes with spot, time and volatility. The stock hedge is held fixed in this example.

**Does a short straddle always make money from theta?** A positive time-decay contribution can be overwhelmed by spot and volatility shocks. The scenario demonstrates that tradeoff; it is not a strategy recommendation.

**What is the market value of a short option?** Negative liability value. Initial cash premium is not added again when calculating the change in mark-to-market value.

**Would this hedge P&L match a bank ledger?** Not without cash financing, dividends, margin, actual executions and settlement conventions. The panel labels these exclusions.

**Why BSM and a tree?** BSM is transparent and fast; the tree provides a different computational mechanism for checking European price convergence. Neither establishes that flat-volatility assumptions fit a real market.

**What would you improve next?** Actual option-chain data and market conventions, implied-volatility smiles, external benchmark alignment, scenario limits and a self-financing dynamic hedge simulation. Avoid adding more charts before validating these foundations.

Be transparent about AI assistance and explain which code and assumptions you have personally reviewed. The strongest demonstration is answering the financial questions without relying on the dashboard.
