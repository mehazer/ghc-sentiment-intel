# User manual

## Dashboard pages

**Overview** — top opportunity with alpha gauge, full alpha ranking (sentiment,
attention, smart money, confidence), the GHC threshold ladder, the current
playbook, live alerts and a trend radar.

**GHC Console** — the trading cockpit. The ladder shows S2/S1/balance/B1/B2 with
your current deviation marked in amber. The action plan lists what to do in the
current zone, in order. Below: open trades, outlier count, unrealised PnL, CSI
and the full trade list with outlier flags.

**Asset detail** — alpha timeline, the four subscores, per-component
contributions and a plain-language "why the score changed" panel.

**Narratives** — the twelve tracked narratives with the assets currently mapped
to each.

**Smart Money** — smart-money score per asset and the composite risk indicator
with its drivers.

**Alerts** — every alert with reason, confidence, expected impact and timestamp.

## Daily routine

1. Open the GHC Console and set your balance line and current equity
   (`POST /api/ghc/balance`, or wire it to your account snapshot job).
2. Read the zone. Between S1 and B1 the rule is hold and police risk: funding,
   daily PnL forecast, PnL > 0, minor adjustments only, scan both baskets.
3. If you are past S1 or below B1, follow the listed ladder: set limits, crop
   outliers, take profit, recalculate CSI and thresholds once filled.
4. Review the outlier list before adding any new risk.
5. Check the Overview ranking for new candidates that align with your zone.

## Reading a score

- **Alpha** is the weighted composite. Above 71 means the components agree.
- **Confidence** tells you how much evidence exists. A high alpha with low
  confidence is a hypothesis, not a trade.
- **Reliability** measures agreement between components. Wide disagreement
  (e.g. attention 95, volume 6) means the move is not confirmed by flow.
- **Explanation** always names the primary driver. If attention is the only
  driver, wait for volume or smart money to confirm.

## Alert interpretation

- **Early accumulation** — attention building while price is still quiet. The
  highest-value alert; check liquidity before sizing.
- **Breakout watch** — new money entering with rising open interest.
- **FOMO warning** — retail extreme while whales sell or funding is stretched.
- **Possible top** — distribution into strength with slowing momentum.

## Outliers

A trade is an outlier when PnL breaches the ATH/ATL condition or falls below the
configured threshold (default −3%). Crop outliers during the S1/S2 and B1/B2
routines, not in the neutral band unless risk is deteriorating.

## Limits

- Scores are probabilistic and depend on ingested data coverage.
- Statements about "smart money" are inferred from flows, not from identified
  counterparties.
- The platform never places orders. Execution stays with you.
