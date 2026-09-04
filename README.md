# FBA Brand Sourcing Scanner (Keepa-powered)

A daily scanning script that queries Keepa for products from specific brands
(e.g. Philips, LEGO, Remington, beauty brands) and outputs a ranked candidate
list — products worth investigating further for FBA sourcing.

## What this does (and doesn't do)

**Does:**
- Queries Keepa's Product Finder for ASINs matching your brand list
- Pulls sales rank, offer count, rating, and price stats for each ASIN
- Scores each product on a simple "opportunity" heuristic (see `scoring.py`)
- Writes a dated CSV (`output/candidates_YYYY-MM-DD.csv`) you can review

**Does NOT do (by design, for v1):**
- Does not know your actual supplier cost — margin isn't calculated, only
  demand/competition signals. You add cost once you've identified a supplier.
- Does not contact suppliers or place any orders.
- Does not check Amazon brand-gating/approval status for you.

## Before you run this

1. **Get a Keepa API key**: https://keepa.com/#!api (paid subscription,
   priced by tokens/minute).
2. **Important — brand authorization**: Philips, LEGO, Remington, and most
   established beauty brands are commonly *gated* on Amazon, meaning you
   need an invoice from an authorized distributor (or brand approval) before
   you're allowed to list them. This tool only tells you what's *worth*
   sourcing — it doesn't confirm you're allowed to source/sell it. Verify
   ungating requirements and get real invoices before buying inventory.
3. Copy `.env.example` to `.env` and fill in your API key.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and add your KEEPA_API_KEY
```

## Verify the API shape first (important)

Keepa's raw JSON field layout can shift between plan types and API versions,
and I (Claude) can't hit the live API to test it in this environment. Before
trusting the scoring output, run:

```bash
python3 debug_inspect.py B0088PUEPK
```

(any real ASIN works) and compare the printed structure against
`constants.py`'s `CSV_TYPE` comments. Adjust indices there if anything looks
off — this is the one part of the script worth double-checking by hand.

## Running it

```bash
python3 main.py
```

This will:
1. Loop through the brands in `config.py`
2. Query Keepa's Product Finder for each
3. Fetch stats for the results
4. Score and rank them
5. Write `output/candidates_<date>.csv`
6. Print the top 10 to your terminal

## Running it daily automatically

Add a cron job (Mac/Linux):

```bash
crontab -e
# run every day at 7am
0 7 * * * cd /path/to/fba-sourcing && /path/to/venv/bin/python3 main.py >> run.log 2>&1
```

On Windows, use Task Scheduler to run `main.py` daily instead.

## Tuning

Edit `config.py`:
- `BRANDS` — your target brand list
- `MAX_SALES_RANK` — ignore products selling too slowly
- `MAX_OFFER_COUNT` — ignore products with too much seller competition
- `MIN_RATING` / `MIN_REVIEWS` — quality floor

Edit `scoring.py` to change how candidates are ranked once you have a feel
for what matters most to you (e.g. weight price stability higher).

## Next steps once this works

- Add a real supplier cost input (CSV or a wholesale API) so the script can
  compute actual margin, not just demand signals.
- Add Slack/email delivery of the daily CSV instead of just writing it locally.
- Add a "seen before" store (SQLite) so you only get *new* candidates each day.
