/* EXAMPLE base CV (anonymized).
   Copy this file to data/base_cv.typ and fill in your own details.
   Keep the canonical structure: == Profile (with the AI comment block),
   == Work Experience with #work(...) calls followed by
   === Job Description / === Notable Achievements bullet databases,
   == Skills. The tailoring prompt in src/cv_tailor.py expects exactly
   these sections and comment blocks.
*/
#import "@preview/basic-resume:0.2.4": *

#let name = "Ad Soyad"
#let location = "Istanbul, TR"
#let email = "ad.soyad@example.com"
#let github = "github.com/adsoyad"
#let linkedin = "linkedin.com/in/adsoyad/"
#let phone = "+90 (5__) ___-____"

#show: resume.with(
  author: name,
  location: location,
  phone: phone,
  accent-color: "#26428b",
  font: "New Computer Modern",
  paper: "us-letter",
  author-position: left,
  personal-info-position: left,
)

#link("mailto:ad.soyad@example.com")[ad.soyad\@example.com]
|
#link("https://github.com/adsoyad")[github.com/adsoyad]
|
#link("https://www.linkedin.com/in/adsoyad/")[linkedin.com/in/adsoyad]

== Profile
/*
== Professional Summary Components for AI
AI bina bloklarini buradan secer; her satir bir alternatiftir.
*/

/*
# --- EXPERIENCE LEVEL & KEY TITLES ---
# Data Engineer
# Business Intelligence Specialist

# --- CORE COMPETENCIES & SKILLS ---
# - data warehousing and ETL/ELT pipeline development
# - cloud data platforms (GCP, BigQuery)
# - process automation and performance optimization
# - business intelligence solutions (Power BI)
*/

Sample Person, a Data Engineer who delivers reliable data pipelines.

== Work Experience
#work(
  title: "Data Engineer",
  location: "Istanbul, TR",
  company: "Ornek Teknoloji A.S.",
  dates: dates-helper(start-date: "Jan 2024", end-date: "Present")
)
=== Job Description
/* DATABASE OF RESPONSIBILITIES (R1-R3):
The AI must select EXACTLY THREE points based on the fitting logic.
*/

// Responsibility 1: Data Pipelines [ETL]
// V_SHORT: Designed and maintained ETL pipelines into the analytical warehouse.
// V_LONG: Designed, developed, and operated end-to-end ETL pipelines that load curated data into the warehouse powering analytics.

// Responsibility 2: BI Dashboards [BI]
// V_SHORT: Built Power BI dashboards for business stakeholders.
// V_LONG: Partnered with business units to translate requirements into self-service dashboards that drove key decisions.

// Responsibility 3: Data Quality [Governance]
// V_SHORT: Implemented data quality checks for critical tables.
// V_LONG: Implemented a data quality monitoring framework with lineage tracking to keep core metrics reliable.

=== Notable Achievements

/* DATABASE OF ACHIEVEMENTS (A1-A2):
The AI must select EXACTLY TWO points.
*/

// Achievement 1: Pipeline Performance [Performance]
// V_SHORT: Cut a 10-hour nightly data refresh down to 2 hours via SQL optimization.
// V_LONG: Re-architected the nightly data refresh process, reducing runtime from 10 to 2 hours with new SQL logic.

// Achievement 2: Warehouse Migration [Migration]
// V_SHORT: Migrated legacy SSIS jobs to the modern cloud warehouse with zero reported downtime.
// V_LONG: Led the migration of legacy SSIS packages into the modern cloud data warehouse with minimal risk.

#work(
  title: "Junior Data Analyst",
  location: "Istanbul, TR",
  company: "Ornek A.S.",
  dates: dates-helper(start-date: "May 2022", end-date: "Jan 2024"),
)
=== Job Description
- Built weekly reporting dashboards in Power BI for operations teams.
- Automated recurring analytical tasks with Python and KNIME workflows.

== Education
#edu(
  institution: "Ornek Universitesi",
  location: "Istanbul, TR",
  dates: dates-helper(start-date: "Sept 2018", end-date: "Jun 2022"),
  degree: "Industrial Engineering, Bachelor's Degree",
  consistent: true
)

== Skills
- *Data Warehousing*: SQL, ETL/ELT, Data Modeling
- *Cloud Technologies*: GCP (BigQuery), Dataflow
- *BI Tools*: Power BI, Dataform
- *Programming*: Python, PySpark
