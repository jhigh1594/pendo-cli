# Pendo API: Historical Snapshots and YoY Comparison

## Summary

**Yes — the Pendo Aggregation API supports historical date ranges.** The CLI can be extended to return past-period data for YoY comparison. The main fix is using **epoch milliseconds** for absolute `first` in `timeSeries`; the CLI currently sends a date string, which the API treats as an expression and can yield empty or wrong results.

## What the docs say

### 1. Aggregation API and timeSeries (source: Adopt Partners API doc)

- Endpoint: `POST https://app.pendo.io/api/v1/aggregation` (main product uses `app.pendo.io`; Adopt uses a different host).
- Request body includes a **pipeline** whose first step is a **source** plus a **timeSeries** object.

**timeSeries shape:**

```json
{
  "period": "dayRange" | "hourRange",
  "first": <timeInMsOrExpression>,
  "count": <numberOfPeriods>
}
```

- **first**: Start of the first period. Either:
  - **Milliseconds since epoch** (number) — use for **absolute** historical ranges (e.g. Q4 2024, Q4 2025).
  - **Expression** (string), e.g. `"now()"` or `"now() - 30*24*60*60*1000"` — use for relative ranges.
- **count**: Number of periods. Positive = forward from `first`; negative = backward from “now” when `first` is `"now()"`.
- **period**: `dayRange` (aligned to account timezone) or `hourRange`.

Documented example for a **fixed date range** (July 10–12, 2015):

```json
{
  "timeSeries": {
    "period": "dayRange",
    "first": 1436553419000,
    "count": 3
  }
}
```

So **historical snapshots are supported** by setting `first` to the start of the desired period in **epoch ms** and `count` to the number of days (or hours).

### 2. Why absolute from_date/to_date can return 0 today

The CLI currently does:

```python
time_series = {"period": "dayRange", "first": from_date, "count": days_span}
```

with `from_date` a string like `"2025-10-01"`. The API doc states that if `first` is a string it is **evaluated as an expression**. A plain date string is not a valid expression, so the API may reject it or interpret it in a way that returns no data. So:

- **Relative** ranges work: `"first": "now()", "count": -7` (last 7 days).
- **Absolute** ranges should use **epoch milliseconds** for `first`, not `"YYYY-MM-DD"`.

### 3. Data retention and “snapshots”

- The API does not define “snapshots” as a separate concept. You get historical data by querying a **past time range** (absolute `first` + `count`).
- How far back data is available is a **subscription/retention** question (not specified in the public doc). For YoY you need at least ~12 months; confirm with Pendo or your contract.

## What we can add

1. **Historical WAU (and events) in the CLI**
   - For `query wau --from-date YYYY-MM-DD --to-date YYYY-MM-DD` (and similarly for events), convert the start date to **epoch milliseconds** (at start of day in the account timezone, or UTC if unknown) and set:
     - `timeSeries.first` = that value
     - `timeSeries.count` = number of days in the range
   - No change to pipeline structure; only the `timeSeries` payload.

2. **YoY comparison**
   - Run two aggregations: one for “this year” (e.g. Q4’25) and one for “prior year” (e.g. Q4’24) using absolute `first` + `count` for each.
   - Either:
     - Add a small “compare” mode that runs both and prints current vs prior, or
     - Document that users run the same command twice with different `--from-date`/`--to-date` and compare output (e.g. `query wau --from-date 2024-10-01 --to-date 2024-12-31` and same for 2025).

3. **Optional: “quarter” shorthand**
   - E.g. `--quarter Q4 --year 2024` that translates to the correct `first` (epoch ms) and `count` for that quarter. Purely convenience on top of absolute ranges.

## Source vs main product

- The **Adopt Partners** doc explicitly describes `timeSeries` and absolute `first` (epoch ms); the same aggregation endpoint and pipeline model are used for the main Pendo product (`app.pendo.io`).
- Public examples (e.g. [pendo-ETL-API-calls](https://github.com/pendo-io/pendo-ETL-API-calls)) mostly show relative `"first": "now()", "count": -N`; the Adopt doc is the clearest on **absolute** ranges.
- Our CLI uses `trackEvents` as the source; the doc uses `events` / `pageEvents` etc. The **timeSeries** contract is shared across sources; only the source name and parameters differ.

## Recommendation

1. **Implement:** In `_query_wau` (and `_query_events` if desired), when `from_date` and `to_date` are provided, set `timeSeries.first` to the **epoch milliseconds** for the start of `from_date` (e.g. midnight UTC or account TZ) and `timeSeries.count` to the number of days. This should fix “absolute range returns 0” and enable historical and YoY queries.
2. **Document:** In the CLI help or README, state that `--from-date` / `--to-date` use absolute ranges and support historical periods for YoY; retention depends on the subscription.
3. **Optional:** Add a `--quarter` / `--year` or “last 92 days” quarter approximation and document that “quarter” is defined that way if Pendo does not expose a native quarter period.

No separate “historical snapshots” API is required; historical behavior is the same API with absolute `first` (epoch ms) and positive `count`.
