# The Price of Prestige

<p>
  <a href="https://aayanahmed20.github.io/stanford-daily-price-of-prestige/">
    <img alt="Live article" src="https://img.shields.io/badge/live_article-GitHub_Pages-8C1515?style=flat&logo=githubpages&logoColor=fff&labelColor=8C1515" />
  </a>
  <a href="https://www.python.org/">
    <img alt="Python 3.12" src="https://img.shields.io/badge/python-3.12-3776AB?style=flat&logo=python&logoColor=fff" />
  </a>
  <a href="https://quarto.org/">
    <img alt="Quarto" src="https://img.shields.io/badge/Quarto-1.10-1496FF?style=flat" />
  </a>
  <a href="https://github.com/aayanahmed20/stanford-daily-price-of-prestige/actions/workflows/ci.yml">
    <img alt="CI" src="https://github.com/aayanahmed20/stanford-daily-price-of-prestige/actions/workflows/ci.yml/badge.svg" />
  </a>
  <a href="LICENSE">
    <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-green.svg" />
  </a>
</p>

**What a Stanford degree is actually worth** — a data-journalism investigation
into the price, aid, and earnings that come with a Stanford education, built on
the U.S. Department of Education's [College Scorecard](https://collegescorecard.ed.gov/)
and inflation-adjusted using the BLS Consumer Price Index.

![Net price by family income: Stanford vs. its peers](./figures/fig_aid_curve.png)

## The story

Published as a full feature article:

**→ [Read the article](https://aayanahmed20.github.io/stanford-daily-price-of-prestige/)**
(plus the [analysis notebook](https://aayanahmed20.github.io/stanford-daily-price-of-prestige/notebooks/notebook.html))

The headline numbers:

- **Expensive on paper, affordable in practice.** Stanford's sticker price is
  $87,833 — 2.8x the national median of $31,112. But the *average net price*
  students actually pay is **$13,807**, *below* the national median of $22,347.
  Families earning under $30,000 pay a **negative** net price: aid exceeds the
  full cost of attendance.
- **The middle class carries the cost.** Net price swings from negative for the
  poorest families to **$53,882** for those earning $110,001+ — a ~$56,000
  swing across the income distribution.
- **The earnings premium is real and partly inherited.** Median earnings ten
  years after entry are **$124,080**, ~2.4x the national median. Even after
  controlling for price, selectivity, Pell share, and family income, Stanford
  graduates out-earn the model's prediction by roughly **47%**.
- **Graduates borrow little.** Median debt is **$12,000** (low-income
  graduates: $6,500) versus a national median of $22,300.
- **Tuition has outpaced inflation — but not unusually so.** Published tuition
  rose from $24,716 (2000-01) to $65,910 (2024-25) in 2025 dollars, roughly in
  line with peer elite privates (+48% vs +46%).

## Reproduce it

Requirements: Python 3.11+ (CI runs 3.12) and [Quarto](https://quarto.org/).

```bash
# 1. Environment
python -m venv .venv
.venv\Scripts\activate            # Windows
source .venv/bin/activate         # macOS/Linux
pip install -r requirements.txt

# 2. Fetch raw data (~0.5 GB the first time) and run the whole pipeline
python -m scripts.download
python -m scripts.validate
python -m scripts.preprocess
python -m scripts.analysis
python -m scripts.visualization

# 3. Tests and lint
python -m pytest
python -m ruff check scripts tests

# 4. Render the article, notebook, and site
quarto render index.qmd
quarto render notebooks/notebook.qmd
quarto render          # full website -> _site/
```

Or with `make`:

```bash
make pipeline          # download -> validate -> preprocess -> analysis -> visualization
make tests
make lint
make render
```

## Repository layout

```
index.qmd                  Feature article (Quarto; the site homepage)
notebooks/notebook.qmd     Reproducible analysis walkthrough (Quarto)
docs/                      Methods, design notes, glossary
scripts/                   The pipeline (download -> visualize)
  download.py              Fetch Scorecard + CPI data (idempotent)
  validate.py              Data-quality checks
  preprocess.py            Clean, merge, inflation-adjust
  analysis.py              Compute all statistics
  visualization.py         Render all figures
tests/                     Unit tests (no network access)
data/                      Raw downloads (git-ignored) + processed tables
figures/                   Generated charts
outputs/                   results.json + tables (the article's source of truth)
```

## Data

| Source | What | Used for |
| --- | --- | --- |
| [College Scorecard](https://collegescorecard.ed.gov/) (June 2026 release) | Most-recent-cohort institution file + 1996-97..2025-26 historical archive | Cross-sectional analysis and the 30-year cost trend |
| FRED / BLS (CPIAUCSL) | Monthly CPI-U, seasonally adjusted | Expressing all dollars in 2025 dollars |

The analysis universe is 2,379 four-year, degree-granting non-profit schools.
Stanford is compared against 16 elite private peers; the earnings/ROI
regression uses 1,079 schools with matched earnings and cost data. Every
statistic in the article is read from `outputs/results.json`, so prose cannot
drift out of sync with the data.

## Notes on the data in this repo

The raw downloads (~0.5 GB) are not committed: `scripts.download` fetches them
from the U.S. Department of Education and FRED, and the Scorecard server blocks
GitHub's cloud IPs, so CI can't reach it either. Instead, the *derived*
artifacts (`data/processed/`, `outputs/`, `figures/`) are committed so the site
builds on Pages without network access. Refresh them with `make pipeline` (or
`make release-data`) and commit the changes.

## License

MIT — see [LICENSE](LICENSE). Data belongs to the U.S. Department of Education
and the U.S. Bureau of Labor Statistics.

*The Price of Prestige* was produced for the [Stanford Daily Tech
Bootcamp](https://github.com/TheStanfordDaily/tech-practicum).
