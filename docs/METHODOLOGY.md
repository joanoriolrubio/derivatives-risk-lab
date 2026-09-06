# Option valuation and risk methodology

## Black–Scholes–Merton

Let S be spot, K strike, T remaining years, σ annual volatility, r continuously compounded rate and q continuous dividend yield.

- d₁ = [ln(S/K) + (r−q+σ²/2)T] / (σ√T)
- d₂ = d₁ − σ√T
- C = S exp(−qT) N(d₁) − K exp(−rT) N(d₂)
- P = K exp(−rT) N(−d₂) − S exp(−qT) N(−d₁)

The normal CDF uses erfc for negative-tail stability. At T=0, pricing returns intrinsic value; derivatives at the payoff kink are not assigned arbitrary values. Spot, strike and volatility must be positive. Rates can be negative. T is nonnegative for pricing and positive for Greeks/inversion.

## Greeks and signs

Let φ be the standard normal density.

- Call delta = exp(−qT) N(d₁); put delta = −exp(−qT) N(−d₁).
- Gamma = exp(−qT) φ(d₁)/(Sσ√T), equal for call and put.
- Vega = S exp(−qT) φ(d₁)√T, equal for call and put.
- Call theta = −S exp(−qT)φ(d₁)σ/(2√T) + qS exp(−qT)N(d₁) − rK exp(−rT)N(d₂).
- Put theta = −S exp(−qT)φ(d₁)σ/(2√T) − qS exp(−qT)N(−d₁) + rK exp(−rT)N(−d₂).
- Call rho = KT exp(−rT)N(d₂); put rho = −KT exp(−rT)N(−d₂).

Theta is ∂V/∂calendar time = −∂V/∂remaining maturity. It is not universally negative for every long option under every rate/dividend configuration. Display scaling is vega×0.01, theta÷365 and rho×0.0001. The engine retains raw derivatives to avoid mixing units in Taylor attribution.

## Portfolio and exact repricing

Value and Greeks sum across signed contracts × shares/contract. All legs share the synthetic underlying and market volatility; strikes and expiries can differ in the API. The UI presets use a common expiry.

Scenario endpoints shock spot multiplicatively, volatility additively in percentage points, rates additively in bp and remaining maturity by elapsed days/365. Exact option P&L is ending market value minus opening market value. Passing a live leg's expiry is rejected because settlement and reinvestment are not modelled. Zero positions are skipped.

## Risk-based explanation

Approximation = Δ ΔS + ½ Γ (ΔS)² + Vega Δσ + Theta Δt + Rho Δr.

All derivatives are evaluated at inception. Δt is positive elapsed time in years. The residual is exact repricing minus this approximation. It contains higher-order terms, vanna/volga and other mixed effects, as well as finite-horizon effects. It is not a bad-input control residual.

The standalone P&L Control project uses exact sequential factor revaluation plus an observed/model mark residual. These are intentionally different questions and should not be confused in an interview.

## Static hedge

At inception trade h=−portfolio delta shares. Initial total delta is then zero in the model; gamma and vega are unchanged. Hedge stock price P&L is h(S₁−S₀). Execution cost is |h|S₀×cost_bp/10000, charged once. Hedged result is exact option P&L plus stock P&L minus cost.

This is not a self-financing total-return hedging backtest. It excludes financing, dividends on stock, margin, transaction costs on option positions, unwind cost and rebalancing. The instantaneous hedge chart has no elapsed time and excludes execution cost. The scenario panel can advance time and clearly labels the remaining exclusions. Initial option premium is already embedded in the opening market value; it must not be added again to market-value P&L.

## Implied volatility

European no-arbitrage bounds are max(0,Se^(−qT)−Ke^(−rT)) < C < Se^(−qT), with the analogous put bounds. Strict endpoints are rejected, as are expiry inversion requests. Bisection searches σ ∈ [0.000001,5.0], stopping when volatility-bracket width is at most 1e-10, with a 200-iteration cap. Premiums outside the finite price bracket fail explicitly.

Vega tends to zero for some deep in/out-of-the-money or near-expiry options; an implied volatility can therefore be poorly identified by rounded prices. A converged numerical solver does not imply reliable market information.

## CRR benchmark

The European tree uses Δt=T/n, u=exp(σ√Δt), d=1/u and risk-neutral p=[exp((r−q)Δt)−d]/(u−d). Payoffs are discounted backwards at exp(−rΔt). Probabilities outside [0,1] fail explicitly. Complexity is O(n²) time and O(n) memory; n is limited to 3,000 for this demonstrator.

The tree is algorithmically separate from the analytic CDF model and converges approximately, with oscillatory discretization error. The default UI uses 600 steps; tests use finer grids. It is not an external production pricer.

## Financial validation

Known numerical prices, put–call parity, arbitrage bounds, call/put Greek relationships, finite differences of all five Greeks, tree convergence and SciPy CDF/PDF comparisons provide complementary checks. Portfolio tests cover signed scaling, zero shocks, execution costs, expiry limits, offsetting legs and losses that remain under delta hedging.
