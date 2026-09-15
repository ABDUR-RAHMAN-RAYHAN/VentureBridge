# VentureBridge

A secure, full-stack startup collaboration platform connecting Founders, Investors, and Job
Seekers — built entirely in **Python (Flask)**, with SQLAlchemy (SQLite by default, MySQL-ready),
HTML/CSS/vanilla JS. "Liquid glass" (glassy + glossy) UI in blue/green, built around the
VentureBridge logo.

## Features implemented

- Registration/login/logout with hashed passwords, rate-limited login (5 attempts / 15 min,
  tracked in DB), session regeneration on login/registration, HttpOnly/SameSite cookies.
- Forgot/reset password with single-use, 1-hour tokens (reset link shown on-page since no SMTP is
  configured — fully testable without an email server).
- Role-based dashboards (Founder / Investor / Job Seeker / Admin) with live Chart.js charts.
- Profile management with a live completion-percentage indicator.
- **Founder identity verification is required** before a founder can list a startup or post a job
  — an unverified founder is redirected straight to the live-photo verification page.
- **Startup listings** — a Trade License upload is mandatory to publish; additional documents
  (Certificate of Incorporation, Tax Registration, Other) can be added anytime. A startup is only
  "Documents Verified" once every submitted document is admin-approved, and **only then does it
  appear in the public directory, landing-page features, or job listings** — unverified startups
  are invisible to everyone except their own founder and admins.
- Public startup & job directories with keyword search, filters, and pagination (both scoped to
  verified/active startups only).
- Job postings, applications with **required CV upload**, duplicate-application prevention, and a
  Submitted → Reviewing → Shortlisted → Rejected/Accepted status pipeline.
- **Investment negotiation workflow** (multi-step, not a single "accept" click):
  1. Investor sends interest with a message.
  2. Founder accepts and submits a **financial distribution proposal** — total amount requested
     plus a line-item breakdown of exactly what it's for.
  3. The investor reviews it and either **accepts** the terms or **sends back changes** (a revised
     total + breakdown); this can go back and forth any number of rounds, with full version
     history preserved.
  4. Once either party accepts the other's current terms, the founder builds a **milestone
     schedule** (amounts must sum to the agreed total) and VentureBridge generates a formal,
     contract-structured **Investment & Funding Agreement** — parties, background, use-of-funds
     breakdown, milestone schedule, benefit terms, representations, a breach/dispute/governing-law
     clause, and platform-role disclosure.
  5. **Both the founder and the investor must individually sign** the agreement (typed legal name
     + explicit confirmation, timestamped) before it becomes active.
  6. Only once **both signatures are in** does VentureBridge create the connection between them and
     unlock messaging — "the journey starts together."
- **Milestone fund release**: only an Admin releases each milestone's funds (never a lump sum,
  and never before the agreement is fully signed); a platform fee percentage is applied and logged
  on every release.
- **Identity verification with 3 required live-captured photos** (via device camera, not file
  upload) for National ID / Passport / Driving License, with a full submission history and
  admin approve/reject-with-reason queue.
- Messaging restricted server-side to users who share a connection (which, per the flow above, only
  exists after a fully-signed agreement).
- Admin panel: user/startup/job activate-deactivate (with confirmation dialogs), document review
  queue, verification review queue, and a full audit log.
- CSRF protection on every form (Flask-WTF), parameterized queries throughout (SQLAlchemy ORM),
  randomized upload filenames, extension + magic-byte file validation, security headers
  (X-Frame-Options, X-Content-Type-Options, Referrer-Policy), graceful error pages.
- Light/dark/system theme toggle, applied before first paint (no flash), glassy+glossy panels in
  both themes, logo watermark, responsive layout.
- Two real AI algorithms — a CSP-based milestone scheduler and a KNN-based startup recommender —
  see the **AI Algorithms** section below for details.

## AI Algorithms

Two genuine, working AI algorithms are implemented (in `algorithms/`), each solving a real
problem in the platform rather than being decorative:

### 1. Constraint Satisfaction Problem (CSP) — Milestone Scheduler
`algorithms/csp_scheduler.py`. When a founder needs to split a funding total into milestone
payments, they can click **"Auto-Generate with CSP Solver"** on the milestone-builder page
instead of doing the arithmetic by hand. This is formulated as a genuine CSP:

- **Variables:** the dollar amount of each milestone
- **Domains:** integers between 10% and 50% of the total (configurable), so no single milestone
  is trivially small or unreasonably large
- **Constraints:** all milestone amounts must sum exactly to the agreed total

It's solved with **backtracking search + forward checking**: before assigning each variable, the
solver computes the feasible interval for that value given what's left to allocate and how many
milestones remain, pruning the domain rather than discovering infeasibility after the fact. If a
requested milestone count is mathematically unsatisfiable (e.g. 11 milestones at a 10% minimum
each, which is already 110%), the solver correctly reports that rather than returning a bad
answer. Candidate values are shuffled so repeated runs surface different valid schedules, not one
fixed even split.

### 2. K-Nearest Neighbors (KNN) — Similar Startups Recommender
`algorithms/knn_recommender.py`. Every startup's public profile page shows a "Similar Startups"
section, ranked by a real KNN search over mixed-type features:

- Industry (categorical), business stage (ordinal), team size and founding year (numeric,
  min-max normalized across the candidate pool), and required skills (compared via Jaccard
  similarity on the skill sets)
- Since the features are mixed types, plain Euclidean distance doesn't apply — the solver uses a
  **Gower distance** (the standard technique for KNN over mixed categorical/numeric data): each
  attribute contributes a distance normalized to [0, 1], averaged into one overall distance
- The K=3 nearest (lowest-distance) startups are shown with a similarity percentage

Both are demonstrated with real data-dependent behavior in the seed data — e.g. GreenTech Solutions
(CleanTech) is recommended alongside SolarGrid Energy (also CleanTech, similar skills) with a much
higher similarity score than MediConnect (HealthTech).

## Setup

1. **Install Python 3.10+** and create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database — SQLite (default, zero setup):** nothing to configure. A file
   `venturebridge.db` will be created automatically.

   **Or MySQL:** create a database and set an environment variable before running the app/seed:
   ```bash
   # macOS/Linux
   export DATABASE_URL="mysql+pymysql://USER:PASSWORD@localhost/venturebridge"
   # Windows (PowerShell)
   $env:DATABASE_URL="mysql+pymysql://USER:PASSWORD@localhost/venturebridge"
   ```
   Then create the empty database first: `CREATE DATABASE venturebridge;`

4. **Seed the database** (creates all tables + realistic demo data):
   ```bash
   python seed.py
   ```

5. **Run the app:**
   ```bash
   python app.py
   ```
   Visit **http://localhost:5000**

6. **For production**, set a real `SECRET_KEY` environment variable, run behind HTTPS (so the
   Secure cookie flag applies), and use a production WSGI server (e.g. `gunicorn app:app`).

## Demo credentials

Password for every demo account: **`Demo@1234`**

| Role       | Email                          | Notes |
|------------|---------------------------------|-------|
| Admin      | admin@venturebridge.demo        | Review queues, user/startup/job management |
| Founder    | aisha@venturebridge.demo        | Identity-verified. Owns GreenTech Solutions (documents verified) + AgriLink Marketplace (pending) |
| Founder    | farhan@venturebridge.demo       | Identity-verified. Owns MediConnect (documents verified) + SolarGrid Energy (documents verified) |
| Investor   | david@venturebridge.demo        | Has a fully signed, active agreement with Aisha (GreenTech), and a separate pending interest sent to Farhan (MediConnect) awaiting his first response |
| Investor   | meera@venturebridge.demo        | Has a request mid-negotiation with Aisha (GreenTech) — she countered the founder's proposal and it's awaiting Aisha's decision |
| Job Seeker | sara@venturebridge.demo         | Has one application already submitted |

## Try the end-to-end story

1. Log in as **Aisha** (founder) → try Dashboard → "List a Startup" — since Aisha is verified this
   works; a brand-new unverified founder would be redirected to identity verification first.
2. Browse Startups while logged out — **GreenTech Solutions, MediConnect, and SolarGrid Energy**
   all appear (documents approved); **AgriLink Marketplace** does not, since it's still pending
   admin review.
3. Open **GreenTech Solutions'** public page and scroll to **"Similar Startups"** — the KNN
   recommender ranks SolarGrid Energy (same CleanTech industry, overlapping skills) noticeably
   higher than MediConnect (different industry).
4. Log in as **Meera** (investor) → Investment Requests → her request to GreenTech is mid-negotiation
   (she sent back a counter-proposal). Log in as **Aisha** to see it from the founder's side —
   accept it, then on the milestone-builder page click **"Auto-Generate with CSP Solver"** to see
   the backtracking solver produce a valid split, before generating the agreement. Then have both
   **Aisha** and **Meera** sign it (in two separate logins) to watch messaging unlock only once
   both signatures are in.
5. Log in as **David** (investor) → My Requests → his GreenTech agreement is already fully signed
   and active — open the formal Investment & Funding Agreement document, and as **Admin**, release
   the next pending milestone.
6. Log in as **David** or **Aisha** → Messages — they're already connected with sample messages
   (because their agreement was fully signed in the seed data).
7. Log in as **Farhan** (founder) → Investment Requests → David's pending interest in MediConnect
   is still waiting for Farhan's initial response — click "Accept & Send Proposal" to try the
   financial-distribution proposal form yourself, then optionally use the CSP solver again when
   you reach the milestone step.
8. As Admin → Audit Log to see every action recorded, including proposal submissions, revisions,
   and signatures.

## Project structure

```
venturebridge/
  app.py              # App factory, security headers, error handlers
  config.py           # Env-driven configuration (SQLite/MySQL)
  extensions.py       # Flask extension instances
  models.py           # SQLAlchemy models (full schema)
  forms.py            # WTForms (validation + CSRF)
  decorators.py       # Role-based access control
  utils.py            # Secure upload handling, audit logging
  seed.py             # Demo data seeding script
  blueprints/          # auth, main, startups, jobs, investment, verification, messaging, admin
  algorithms/          # CSP milestone scheduler, KNN startup recommender
  templates/           # Jinja2 templates (glassy-glossy UI)
  static/
    css/style.css      # Liquid-glass theme
    js/                # theme toggle, webcam capture, misc UI
    img/logo.png        # VentureBridge logo
    uploads/            # Runtime file uploads (documents, cv, verification, logos)
```

## Notes on scope

- This is not a real payment/financial transaction system — the milestone "funding" workflow
  records amounts, terms, and release events for transparency and trust-building; it does not move
  real money. Wire actual payment rails in only with proper regulatory/legal review.
- No social login, no automated government ID verification, no AI/ML matching — per the original
  brief, out of scope for this build.
- The camera-based live-photo capture requires the browser to grant camera permission; VentureBridge
  requests it only on the verification page (see the `Permissions-Policy` header in `app.py`).
