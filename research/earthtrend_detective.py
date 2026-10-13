import marimo

__generated_with = "0.25.0"
app = marimo.App(width="full")


@app.cell
def _():
    import json
    from pathlib import Path

    import marimo as mo
    import pandas as pd

    return Path, json, mo, pd


@app.cell
def _(mo):
    mo.md("""
    # 🌍 EARTH TREND DETECTIVE

    ## Case #001 — Jharkhand, India

    **Question:**

    Is Jharkhand experiencing a long-term soil-moisture drying trend?

    ---

    ### Evidence sources

    - **NASA SMAP** — soil moisture
    - **NASA GPM IMERG** — rainfall
    - Statistical trend analysis
    - Extreme-event analysis
    - Spatial rainfall–soil-moisture analysis

    This interactive investigation uses the **validated EarthTrend
    scientific pipeline** and its frozen analysis outputs.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    <div style="
        margin:24px 0 28px 0;
        padding:22px;
        border:1px solid #ddd;
        border-radius:16px;
    ">

    <div style="
        font-size:13px;
        font-weight:700;
        letter-spacing:1px;
        margin-bottom:8px;
    ">
    🕵️ INVESTIGATION ROADMAP
    </div>

    <div style="
        font-size:22px;
        font-weight:700;
        margin-bottom:18px;
    ">
    Case #001 — Jharkhand
    </div>

    <div style="
        display:grid;
        grid-template-columns:repeat(3, minmax(150px, 1fr));
        gap:10px;
        margin-bottom:10px;
    ">

    <div style="padding:14px;border:1px solid #ddd;border-radius:10px;">
    <b>01 — WHEN</b><br>
    Timeline
    </div>

    <div style="padding:14px;border:1px solid #ddd;border-radius:10px;">
    <b>02 — WHERE</b><br>
    Spatial evidence
    </div>

    <div style="padding:14px;border:1px solid #ddd;border-radius:10px;">
    <b>03 — EXTREMES</b><br>
    Dry / wet events
    </div>

    </div>

    <div style="
        text-align:center;
        font-size:20px;
        margin:4px 0;
    ">
    ↓
    </div>

    <div style="
        display:grid;
        grid-template-columns:repeat(3, minmax(150px, 1fr));
        gap:10px;
    ">

    <div style="padding:14px;border:1px solid #ddd;border-radius:10px;">
    <b>04 — RAINFALL LINK</b><br>
    Cross-variable evidence
    </div>

    <div style="padding:14px;border:1px solid #ddd;border-radius:10px;">
    <b>05 — TREND</b><br>
    Statistical test
    </div>

    <div style="padding:14px;border:1px solid #222;border-radius:10px;">
    <b>🔬 FINAL VERDICT</b><br>
    Evidence synthesis
    </div>

    </div>

    </div>
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    <div style="
        margin:10px 0 28px 0;
        padding:12px 14px;
        border:1px solid #ddd;
        border-radius:12px;
        overflow-x:auto;
    ">

    <div style="
        display:flex;
        align-items:center;
        justify-content:center;
        gap:8px;
        min-width:720px;
        font-size:13px;
        font-weight:700;
    ">

    <span style="padding:8px 12px;border:1px solid #ddd;border-radius:8px;">
    01 WHEN
    </span>

    <span>→</span>

    <span style="padding:8px 12px;border:1px solid #ddd;border-radius:8px;">
    02 WHERE
    </span>

    <span>→</span>

    <span style="padding:8px 12px;border:1px solid #ddd;border-radius:8px;">
    03 EXTREMES
    </span>

    <span>→</span>

    <span style="padding:8px 12px;border:1px solid #ddd;border-radius:8px;">
    04 RAINFALL
    </span>

    <span>→</span>

    <span style="padding:8px 12px;border:1px solid #ddd;border-radius:8px;">
    05 TREND
    </span>

    <span>→</span>

    <span style="
        padding:8px 12px;
        border:1px solid #222;
        border-radius:8px;
    ">
    🔬 VERDICT
    </span>

    </div>

    </div>
    """)
    return


@app.cell
def _(Path):
    BASE = Path(__file__).resolve().parent.parent

    ANALYSIS = (
        BASE
        / "data"
        / "analysis"
    )

    FIGURES = ANALYSIS / "figures"
    return ANALYSIS, FIGURES


@app.cell
def _(ANALYSIS, json):
    final_evidence_file = (
        ANALYSIS
        / "earthtrend_final_evidence.json"
    )

    with open(
        final_evidence_file,
        "r",
        encoding="utf-8"
    ) as final_file:
        final_evidence = json.load(
            final_file
        )
    return (final_evidence,)


@app.cell
def _(ANALYSIS, json):
    trend_file = (
        ANALYSIS
        / "smap_trend_manifest.json"
    )

    with open(
        trend_file,
        "r",
        encoding="utf-8"
    ) as trend_file_handle:

        trend = json.load(
            trend_file_handle
        )
    return (trend,)


@app.cell
def _(final_evidence, mo, trend):
    state_trend = trend["state_trend"]

    period_start = trend[
        "source_period"
    ]["start"]

    period_end = trend[
        "source_period"
    ]["end"]

    cells = int(
        trend["spatial_cells"]
    )

    records = int(
        trend["records"]
    )

    slope = float(
        state_trend[
            "sen_slope_per_year"
        ]
    )

    tau = float(
        state_trend[
            "kendall_tau"
        ]
    )

    p_value = float(
        state_trend[
            "p_value"
        ]
    )

    significant = bool(
        state_trend[
            "significant_at_0_05"
        ]
    )

    status = final_evidence.get(
        "status",
        "UNKNOWN"
    )

    mo.md(
        f"""
        ## 🔬 Investigation Status

        | Metric | Result |
        |---|---:|
        | Study period | **{period_start} → {period_end}** |
        | SMAP cells | **{cells:,}** |
        | Cell-month records | **{records:,}** |
        | Sen slope / year | **{slope:.9f}** |
        | Kendall τ | **{tau:.6f}** |
        | Kendall p-value | **{p_value:.6f}** |
        | Significant long-term trend | **{significant}** |
        | Final evidence status | **{status}** |

        ---

        ### Current scientific interpretation

        **No statistically significant long-term monotonic drying
        trend was detected in the analyzed SMAP record.**

        The negative Sen slope is very small, and the Kendall
        p-value is far above the 0.05 significance threshold.
        """
    )
    return


@app.cell
def _(final_evidence, mo, trend):
    kpi_state_trend = trend["state_trend"]

    kpi_period_start = trend[
        "source_period"
    ]["start"]

    kpi_period_end = trend[
        "source_period"
    ]["end"]

    kpi_cells = int(
        trend["spatial_cells"]
    )

    kpi_records = int(
        trend["records"]
    )

    kpi_p_value = float(
        kpi_state_trend["p_value"]
    )

    kpi_rainfall_r = float(
        final_evidence[
            "EVIDENCE"
        ]["RAINFALL_SAME_MONTH"][
            "standardized_pearson_r"
        ]
    )

    mo.md(
        f"""
        <div style="
            display:grid;
            grid-template-columns:repeat(5, minmax(140px, 1fr));
            gap:12px;
            margin:18px 0 24px 0;
        ">

        <div style="
            padding:18px;
            border:1px solid #ddd;
            border-radius:12px;
            text-align:center;
        ">
            <div style="font-size:13px;">📅 STUDY PERIOD</div>
            <div style="font-size:24px;font-weight:700;">
                {kpi_period_start[:7]}
            </div>
            <div style="font-size:13px;">
                → {kpi_period_end[:7]}
            </div>
        </div>

        <div style="
            padding:18px;
            border:1px solid #ddd;
            border-radius:12px;
            text-align:center;
        ">
            <div style="font-size:13px;">🛰️ SMAP CELLS</div>
            <div style="font-size:28px;font-weight:700;">
                {kpi_cells:,}
            </div>
        </div>

        <div style="
            padding:18px;
            border:1px solid #ddd;
            border-radius:12px;
            text-align:center;
        ">
            <div style="font-size:13px;">📊 CELL-MONTH RECORDS</div>
            <div style="font-size:28px;font-weight:700;">
                {kpi_records:,}
            </div>
        </div>

        <div style="
            padding:18px;
            border:1px solid #ddd;
            border-radius:12px;
            text-align:center;
        ">
            <div style="font-size:13px;">📉 TREND p-VALUE</div>
            <div style="font-size:28px;font-weight:700;">
                {kpi_p_value:.3f}
            </div>
            <div style="font-size:13px;">
                Not significant
            </div>
        </div>

        <div style="
            padding:18px;
            border:1px solid #ddd;
            border-radius:12px;
            text-align:center;
        ">
            <div style="font-size:13px;">🌧️ RAINFALL LINK</div>
            <div style="font-size:28px;font-weight:700;">
                r = {kpi_rainfall_r:.3f}
            </div>
            <div style="font-size:13px;">
                Same-month Pearson
            </div>
        </div>

        </div>
        """
    )
    return


@app.cell
def _(final_evidence, mo, trend):
    glance_evidence = final_evidence["EVIDENCE"]
    glance_interpretation = final_evidence["INTERPRETATION"]

    glance_trend = trend["state_trend"]
    glance_trend_p = float(glance_trend["p_value"])
    glance_trend_significant = bool(
        glance_trend["significant_at_0_05"]
    )

    glance_rain = glance_evidence["RAINFALL_SAME_MONTH"]
    glance_rain_r = float(
        glance_rain["standardized_pearson_r"]
    )

    glance_acf = glance_evidence[
        "RAINFALL_AUTOCORRELATION_AWARE"
    ]
    glance_overall = next(
        item for item in glance_acf["results"]
        if item["analysis"] == "overall_monthly"
    )
    glance_adjusted_p = float(glance_overall["adjusted_p"])

    glance_spatial = glance_evidence["RAINFALL_SPATIAL"]
    glance_spatial_r = float(glance_spatial["pearson_r_mean"])

    glance_extremes = glance_evidence["EXTREME_EVENTS"]
    glance_dry_months = int(glance_extremes["dry_candidate_months"])
    glance_wet_months = int(glance_extremes["wet_candidate_months"])

    glance_spatial_trend = glance_evidence["SPATIAL_TREND"]
    glance_hotspots = int(
        glance_spatial_trend["spatial_hotspot_results"]
    )

    glance_trend_label = (
        "Significant trend detected"
        if glance_trend_significant
        else "Not statistically significant"
    )

    mo.md(
        f"""
        ## 🔎 Scientific Evidence at a Glance

        <div style="
            display:grid;
            grid-template-columns:repeat(auto-fit,minmax(190px,1fr));
            gap:14px;
            margin:18px 0;
        ">

        <div style="padding:18px;border:1px solid #d1d5db;border-radius:14px;">
            <div style="font-size:13px;">📉 LONG-TERM TREND</div>
            <div style="font-size:28px;font-weight:750;margin:8px 0;">
                p = {glance_trend_p:.3f}
            </div>
            <div style="font-size:13px;">{glance_trend_label}</div>
        </div>

        <div style="padding:18px;border:1px solid #d1d5db;border-radius:14px;">
            <div style="font-size:13px;">🌧️ SAME-MONTH RAINFALL LINK</div>
            <div style="font-size:28px;font-weight:750;margin:8px 0;">
                r = {glance_rain_r:.3f}
            </div>
            <div style="font-size:13px;">Adjusted p = {glance_adjusted_p:.2e}</div>
        </div>

        <div style="padding:18px;border:1px solid #d1d5db;border-radius:14px;">
            <div style="font-size:13px;">🗺️ SPATIAL ASSOCIATION</div>
            <div style="font-size:28px;font-weight:750;margin:8px 0;">
                r = {glance_spatial_r:.3f}
            </div>
            <div style="font-size:13px;">Mean across 984 mapped SMAP cells</div>
        </div>

        <div style="padding:18px;border:1px solid #d1d5db;border-radius:14px;">
            <div style="font-size:13px;">🔴 DRY EVENT CANDIDATES</div>
            <div style="font-size:28px;font-weight:750;margin:8px 0;">
                {glance_dry_months}
            </div>
            <div style="font-size:13px;">Months meeting the analysis threshold</div>
        </div>

        <div style="padding:18px;border:1px solid #d1d5db;border-radius:14px;">
            <div style="font-size:13px;">🔵 WET EVENT CANDIDATES</div>
            <div style="font-size:28px;font-weight:750;margin:8px 0;">
                {glance_wet_months}
            </div>
            <div style="font-size:13px;">Months meeting the analysis threshold</div>
        </div>

        <div style="padding:18px;border:1px solid #d1d5db;border-radius:14px;">
            <div style="font-size:13px;">📍 SPATIAL TREND HOTSPOTS</div>
            <div style="font-size:28px;font-weight:750;margin:8px 0;">
                {glance_hotspots}
            </div>
            <div style="font-size:13px;">After Benjamini–Hochberg FDR correction</div>
        </div>

        </div>

        ### What does the evidence mean?

        The analyzed record does **not** show a statistically significant
        long-term monotonic soil-moisture decline. However, rainfall and
        soil-moisture anomalies have a strong positive same-month association,
        and the association remains statistically significant under the
        project's effective-sample-size adjustment.

        The analysis also identifies dry and wet extreme-event candidates.
        These findings describe variability and association; they do not
        establish that rainfall alone causes the observed soil-moisture changes.

        <div style="font-size:12px;color:#777;margin-top:10px;">
        Rainfall comparison period: {glance_rain["period_start"][:7]}
        to {glance_rain["period_end"][:7]}.
        The long-term SMAP trend uses a longer study period.
        </div>
        """
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ## 🧪 Scientific Methodology & Limitations

    ### 1. Data sources and study periods

    | Dataset | Role | Period |
    |---|---|---|
    | NASA SMAP L4 | Soil-moisture trend and extreme-event analysis | Apr 2015 – Sep 2026 |
    | NASA GPM IMERG | Monthly rainfall and rainfall–soil-moisture association | Apr 2015 – Sep 2025 |

    The rainfall comparison uses the overlapping observation period.
    The two datasets have different spatial resolutions and are mapped
    to corresponding grid cells for comparison.

    ### 2. Statistical methods

    - **Sen's slope:** estimates the magnitude and direction of a trend.
    - **Mann–Kendall test:** evaluates evidence for a monotonic trend.
    - **Pearson correlation:** measures the strength and direction of a
      linear rainfall–soil-moisture association.
    - **Autocorrelation-aware analysis:** adjusts the rainfall
      association test for temporal dependence using an effective
      sample size.
    - **Benjamini–Hochberg FDR correction:** adjusts groups of statistical
      tests to control the expected false-discovery rate.
    - **Standardized anomalies:** help identify unusually dry or wet
      cell-months relative to the analysis baseline.

    ### 3. What the findings support

    The state-level analysis does not detect a statistically significant
    long-term monotonic soil-moisture trend at the 0.05 significance
    level. Rainfall and soil-moisture anomalies show a strong positive
    same-month association, which remains statistically significant
    under the project's autocorrelation-aware adjustment.

    ### 4. Limitations and interpretation

    - **Association is not causation.** Correlation alone cannot establish
      that rainfall causes every observed soil-moisture change.
    - **Spatial dependence:** neighboring cells and cells mapped to the
      same coarse rainfall grid are not fully independent observations.
    - **Resolution mismatch:** spatial mapping can introduce uncertainty
      because rainfall and soil-moisture grids differ in resolution.
    - **Statistical significance is not practical significance:** a
      p-value does not measure the size or importance of an effect.
    - **Extreme-event candidates depend on thresholds:** the event counts
      reflect the project's chosen anomaly thresholds and should not
      automatically be interpreted as independently verified droughts
      or floods.
    - **No detected trend does not prove no change:** it means this
      analysis did not find sufficient statistical evidence for a
      monotonic state-level trend over the analyzed period.

    **Interpretation rule:** conclusions should remain limited to the
    data coverage, statistical methods, and assumptions documented in
    this project.
    """)
    return


@app.cell
def _(FIGURES, mo):
    figure_files = sorted(
        FIGURES.glob(
            "earthtrend_*.png"
        )
    )

    if figure_files:
        rows = "\n".join(
            f"- `{figure.name}`"
            for figure in figure_files
        )
    else:
        rows = "- No evidence figures found."

    mo.md(
        f"""
        ## 📊 Existing Evidence Figures

        The scientific pipeline has produced:

        {rows}

        **Figures found:** {len(figure_files)}

        These figures are generated from the validated
        analysis pipeline and are separate from this
        interactive Marimo investigation.
        """
    )
    return


@app.cell
def _(final_evidence, mo, trend):
    scoreboard_trend = trend["state_trend"]

    scoreboard_p = float(
        scoreboard_trend["p_value"]
    )

    scoreboard_rainfall = float(
        final_evidence[
            "EVIDENCE"
        ]["RAINFALL_SAME_MONTH"][
            "standardized_pearson_r"
        ]
    )

    scoreboard_spatial = float(
        final_evidence[
            "EVIDENCE"
        ]["RAINFALL_SPATIAL"][
            "pearson_r_mean"
        ]
    )

    scoreboard_dry = int(
        final_evidence[
            "EVIDENCE"
        ]["EXTREME_EVENTS"][
            "dry_candidate_months"
        ]
    )

    scoreboard_wet = int(
        final_evidence[
            "EVIDENCE"
        ]["EXTREME_EVENTS"][
            "wet_candidate_months"
        ]
    )

    scoreboard_hotspots = int(
        final_evidence[
            "EVIDENCE"
        ]["SPATIAL_TREND"][
            "spatial_hotspot_results"
        ]
    )

    mo.md(
        f"""
        <div style="
            margin:24px 0 30px 0;
            padding:22px;
            border:1px solid #ddd;
            border-radius:16px;
        ">

        <div style="
            font-size:13px;
            font-weight:700;
            letter-spacing:1px;
            margin-bottom:8px;
        ">
        🧾 EVIDENCE SCOREBOARD
        </div>

        <div style="
            font-size:22px;
            font-weight:700;
            margin-bottom:18px;
        ">
        What does the evidence say?
        </div>

        <div style="
            display:grid;
            grid-template-columns:repeat(3, minmax(180px, 1fr));
            gap:12px;
        ">

        <div style="padding:16px;border:1px solid #ddd;border-radius:12px;">
        <div style="font-size:13px;">🌧️ RAINFALL ASSOCIATION</div>
        <div style="font-size:24px;font-weight:700;margin-top:6px;">
        r = {scoreboard_rainfall:.3f}
        </div>
        <div style="font-size:13px;">Same-month Pearson</div>
        </div>

        <div style="padding:16px;border:1px solid #ddd;border-radius:12px;">
        <div style="font-size:13px;">🗺️ SPATIAL RELATIONSHIP</div>
        <div style="font-size:24px;font-weight:700;margin-top:6px;">
        r = {scoreboard_spatial:.3f}
        </div>
        <div style="font-size:13px;">Mean spatial Pearson</div>
        </div>

        <div style="padding:16px;border:1px solid #ddd;border-radius:12px;">
        <div style="font-size:13px;">📉 LONG-TERM TREND</div>
        <div style="font-size:24px;font-weight:700;margin-top:6px;">
        p = {scoreboard_p:.3f}
        </div>
        <div style="font-size:13px;">Not significant</div>
        </div>

        <div style="padding:16px;border:1px solid #ddd;border-radius:12px;">
        <div style="font-size:13px;">🔥 EXTREME DRY</div>
        <div style="font-size:24px;font-weight:700;margin-top:6px;">
        {scoreboard_dry}
        </div>
        <div style="font-size:13px;">Event candidates</div>
        </div>

        <div style="padding:16px;border:1px solid #ddd;border-radius:12px;">
        <div style="font-size:13px;">💧 EXTREME WET</div>
        <div style="font-size:24px;font-weight:700;margin-top:6px;">
        {scoreboard_wet}
        </div>
        <div style="font-size:13px;">Event candidates</div>
        </div>

        <div style="padding:16px;border:1px solid #222;border-radius:12px;">
        <div style="font-size:13px;">📍 FDR SPATIAL HOTSPOTS</div>
        <div style="font-size:24px;font-weight:700;margin-top:6px;">
        {scoreboard_hotspots}
        </div>
        <div style="font-size:13px;">Robust hotspots detected</div>
        </div>

        </div>

        <div style="
            margin-top:16px;
            padding:14px 16px;
            border:1px solid #ddd;
            border-radius:10px;
            font-size:14px;
        ">
        🔬 <b>Reading the scoreboard:</b>
        the evidence points to rainfall-linked variability
        and episodic extremes, while the long-term drying
        signal is not statistically significant.
        </div>

        </div>
        """
    )
    return


@app.cell
def _(ANALYSIS, pd):
    timeline_file = (
        ANALYSIS
        / "earthtrend_timeline.csv"
    )

    timeline = pd.read_csv(
        timeline_file,
        parse_dates=["date"]
    )

    timeline = timeline.sort_values(
        "date"
    ).reset_index(drop=True)
    return (timeline,)


@app.cell
def _(mo, timeline):
    mo.md(f"""
    ## ⏱️ WHEN? — Soil-Moisture Timeline

    The validated timeline contains:

    - **{len(timeline):,} monthly observations**
    - **{timeline["date"].min().date()} → {timeline["date"].max().date()}**
    - **{timeline["cells"].iloc[0]:,} SMAP cells per month**

    The chart below uses the frozen
    `earthtrend_timeline.csv` analysis output.
    """)
    return


@app.cell
def _(mo, timeline):
    chart = mo.ui.altair_chart(
        chart=(
            __import__("altair")
            .Chart(timeline)
            .mark_line()
            .encode(
                x=__import__("altair").X(
                    "date:T",
                    title="Date"
                ),
                y=__import__("altair").Y(
                    "soil_moisture_mean:Q",
                    title="Mean soil moisture (m³/m³)"
                ),
                tooltip=[
                    __import__("altair").Tooltip(
                        "date:T",
                        title="Date"
                    ),
                    __import__("altair").Tooltip(
                        "soil_moisture_mean:Q",
                        title="Mean soil moisture",
                        format=".4f"
                    ),
                    __import__("altair").Tooltip(
                        "climatology_mean:Q",
                        title="Climatology",
                        format=".4f"
                    ),
                    __import__("altair").Tooltip(
                        "anomaly:Q",
                        title="Anomaly",
                        format=".4f"
                    ),
                    __import__("altair").Tooltip(
                        "standardized_anomaly:Q",
                        title="Standardized anomaly",
                        format=".2f"
                    ),
                    __import__("altair").Tooltip(
                        "season:N",
                        title="Season"
                    ),
                ],
            )
            .properties(
                height=420,
                title="Jharkhand monthly soil moisture"
            )
            .interactive()
        )
    )

    chart
    return


@app.cell
def _(mo, timeline):
    anomaly_chart = mo.ui.altair_chart(
        chart=(
            __import__("altair")
            .Chart(timeline)
            .mark_line()
            .encode(
                x=__import__("altair").X(
                    "date:T",
                    title="Date"
                ),
                y=__import__("altair").Y(
                    "standardized_anomaly:Q",
                    title="Standardized anomaly"
                ),
                tooltip=[
                    __import__("altair").Tooltip(
                        "date:T",
                        title="Date"
                    ),
                    __import__("altair").Tooltip(
                        "standardized_anomaly:Q",
                        title="Z-score",
                        format=".2f"
                    ),
                    __import__("altair").Tooltip(
                        "anomaly_class:N",
                        title="Class"
                    ),
                    __import__("altair").Tooltip(
                        "season:N",
                        title="Season"
                    ),
                ],
            )
            .properties(
                height=360,
                title="Jharkhand soil-moisture anomaly"
            )
            .interactive()
        )
    )

    anomaly_chart
    return


@app.cell
def _(mo):
    mo.md("""
    ### How to read this evidence

    **Top chart — actual soil moisture**

    Shows how the observed monthly state-average soil moisture
    changes through time.

    **Bottom chart — standardized anomaly**

    Shows departure from the calendar-month climatological normal.

    - Around **0** → near normal
    - Below **−2** → extreme dry
    - Above **+2** → extreme wet

    This distinction matters because a low-value month is not
    automatically an abnormal dry event; it must be compared
    with its normal seasonal baseline.
    """)
    return


@app.cell
def _(ANALYSIS, pd):
    spatial_file = (
        ANALYSIS
        / "smap_gpm_spatial_correlation.csv"
    )

    spatial = pd.read_csv(
        spatial_file
    )

    spatial = spatial.sort_values(
        "pearson_r"
    ).reset_index(drop=True)
    return (spatial,)


@app.cell
def _(mo, spatial):
    mo.md(f"""
    ## 📍 WHERE? — Rainfall–Soil-Moisture Spatial Evidence

    The validated spatial analysis contains:

    - **{spatial["smap_cell"].nunique():,} SMAP cells**
    - **Mean Pearson r = {spatial["pearson_r"].mean():.4f}**
    - **Median Pearson r = {spatial["pearson_r"].median():.4f}**
    - **{(spatial["pearson_r"] > 0).mean() * 100:.1f}% positive correlations**

    Each point represents one SMAP cell. The correlation measures
    how its standardized soil-moisture anomalies relate to the
    corresponding GPM rainfall anomalies over the common analysis
    period.

    **Important:** correlation does not establish causality.
    """)
    return


@app.cell
def _(mo, spatial):
    alt = __import__("altair")

    spatial_chart = (
        alt.Chart(spatial)
        .mark_circle(size=55)
        .encode(
            x=alt.X(
                "smap_longitude:Q",
                title="Longitude"
            ),
            y=alt.Y(
                "smap_latitude:Q",
                title="Latitude"
            ),
            color=alt.Color(
                "pearson_r:Q",
                title="Pearson r",
                scale=alt.Scale(
                    domain=[0.5, 0.8]
                )
            ),
            tooltip=[
                alt.Tooltip(
                    "smap_cell:N",
                    title="SMAP cell"
                ),
                alt.Tooltip(
                    "smap_latitude:Q",
                    title="Latitude",
                    format=".4f"
                ),
                alt.Tooltip(
                    "smap_longitude:Q",
                    title="Longitude",
                    format=".4f"
                ),
                alt.Tooltip(
                    "pearson_r:Q",
                    title="Pearson r",
                    format=".3f"
                ),
                alt.Tooltip(
                    "spearman_rho:Q",
                    title="Spearman rho",
                    format=".3f"
                ),
                alt.Tooltip(
                    "mapping_distance_km:Q",
                    title="Mapping distance (km)",
                    format=".2f"
                ),
                alt.Tooltip(
                    "gpm_cell:N",
                    title="GPM cell"
                ),
            ],
        )
        .properties(
            height=500,
            title="Jharkhand rainfall–soil-moisture spatial correlation"
        )
        .interactive()
    )

    mo.ui.altair_chart(
        spatial_chart
    )
    return


@app.cell
def _(mo, spatial):
    strongest = spatial.loc[
        spatial["pearson_r"].idxmax()
    ]

    weakest = spatial.loc[
        spatial["pearson_r"].idxmin()
    ]

    mo.md(
        f"""
        ### Spatial evidence summary

        **Correlation range**

        - Lowest Pearson r: **{weakest["pearson_r"]:.3f}**
        - Highest Pearson r: **{strongest["pearson_r"]:.3f}**
        - Mean Pearson r: **{spatial["pearson_r"].mean():.3f}**

        The important pattern is that the correlations are consistently
        positive across the mapped SMAP cells rather than being confined
        to a small isolated location.

        The GPM rainfall grid is coarser than the SMAP grid, so multiple
        SMAP cells can share the same GPM cell. Therefore these 984
        spatial correlations should not be interpreted as 984 fully
        independent experiments.
        """
    )
    return


@app.cell
def _(ANALYSIS, pd):
    extreme_file = (
        ANALYSIS
        / "smap_extreme_monthly_summary.csv"
    )

    extremes = pd.read_csv(
        extreme_file,
        parse_dates=["date"]
    )
    return (extremes,)


@app.cell
def _(extremes, mo):
    dry_candidates = int(
        (
            (extremes["dry_extreme_cells"] >= 50)
        ).sum()
    )

    wet_candidates = int(
        (
            (extremes["wet_extreme_cells"] >= 50)
        ).sum()
    )

    max_dry = int(
        extremes["dry_extreme_cells"].max()
    )

    max_wet = int(
        extremes["wet_extreme_cells"].max()
    )

    mo.md(
        f"""
        ## 🌡️ EXTREMES — Soil-Moisture Events

        The validated extreme-event analysis identifies months where
        at least **5% of the 984 SMAP cells** were simultaneously
        classified as extreme dry or extreme wet.

        ### Event evidence

        - **Dry event candidates:** {dry_candidates}
        - **Wet event candidates:** {wet_candidates}
        - **Maximum dry-affected cells:** {max_dry:,}
        - **Maximum wet-affected cells:** {max_wet:,}

        **Event threshold:** at least 50 SMAP cells in the same direction.

        This is an analytical event definition, not a claim that every
        extreme month represents a disaster.
        """
    )
    return


@app.cell
def _(extremes, mo):
    event_table = extremes.loc[
        extremes["event_candidate"] == True,
        [
            "date",
            "event_direction",
            "dry_extreme_cells",
            "dry_extreme_fraction",
            "dry_mean_z",
            "dry_severity",
            "wet_extreme_cells",
            "wet_extreme_fraction",
            "wet_mean_z",
            "wet_severity",
        ],
    ].copy()

    event_table["date"] = (
        event_table["date"]
        .dt.strftime("%Y-%m")
    )

    event_table = event_table.sort_values(
        "date"
    )

    mo.ui.table(
        event_table,
        selection=None
    )
    return


@app.cell
def _(extremes, mo):
    extreme_chart_data = extremes.copy()

    extreme_chart_data["date"] = (
        extreme_chart_data["date"]
        .dt.strftime("%Y-%m")
    )

    extreme_alt = __import__("altair")

    extreme_chart = (
        extreme_alt.Chart(extreme_chart_data)
        .transform_fold(
            [
                "dry_extreme_cells",
                "wet_extreme_cells",
            ],
            as_=["type", "cells"]
        )
        .mark_line()
        .encode(
            x=extreme_alt.X(
                "date:N",
                title="Month",
                sort=None
            ),
            y=extreme_alt.Y(
                "cells:Q",
                title="Extreme cells"
            ),
            color=extreme_alt.Color(
                "type:N",
                title="Extreme type"
            ),
            tooltip=[
                extreme_alt.Tooltip(
                    "date:N",
                    title="Month"
                ),
                extreme_alt.Tooltip(
                    "type:N",
                    title="Type"
                ),
                extreme_alt.Tooltip(
                    "cells:Q",
                    title="Cells"
                ),
            ],
        )
        .properties(
            height=400,
            title="Spatial extent of soil-moisture extremes"
        )
        .interactive()
    )

    mo.ui.altair_chart(extreme_chart)
    return


@app.cell
def _(extremes, mo):
    max_dry_row = extremes.loc[
        extremes["dry_extreme_cells"].idxmax()
    ]

    max_wet_row = extremes.loc[
        extremes["wet_extreme_cells"].idxmax()
    ]

    mo.md(
        f"""
        ### Strongest observed spatial extremes

        **Dry:** {max_dry_row["date"].strftime("%Y-%m")}
        affected **{int(max_dry_row["dry_extreme_cells"]):,} cells**
        ({max_dry_row["dry_extreme_fraction"] * 100:.1f}% of Jharkhand).

        **Wet:** {max_wet_row["date"].strftime("%Y-%m")}
        affected **{int(max_wet_row["wet_extreme_cells"]):,} cells**
        ({max_wet_row["wet_extreme_fraction"] * 100:.1f}% of Jharkhand).

        These results demonstrate that the record contains substantial
        episodic spatial extremes even though the long-term trend test
        does not show a statistically significant monotonic drying trend.
        """
    )
    return


@app.cell
def _(ANALYSIS, pd):
    rainfall_month_file = (
        ANALYSIS
        / "smap_gpm_common_months.csv"
    )

    lag_file = (
        ANALYSIS
        / "smap_gpm_lag_correlation.csv"
    )

    rainfall_months = pd.read_csv(
        rainfall_month_file,
        parse_dates=["date"]
    )

    lag_results = pd.read_csv(
        lag_file
    )
    return lag_results, rainfall_months


@app.cell
def _(mo):
    same_month_r = 0.7135358910048899
    same_month_p = 6.877127936542278e-21

    adjusted_p = 2.1999110689728813e-14

    mo.md(
        f"""
        ## 🌧️ RAINFALL LINK — Cross-Variable Evidence

        SMAP soil-moisture anomalies and GPM rainfall anomalies show a
        strong positive same-month relationship.

        ### Same-month evidence

        - **Pearson r:** {same_month_r:.3f}
        - **Raw p-value:** {same_month_p:.2e}
        - **Autocorrelation-adjusted p-value:** {adjusted_p:.2e}

        The association remains statistically significant after the
        effective-sample-size adjustment for temporal autocorrelation.

        **Important:** this is an association, not proof of causality.
        """
    )
    return


@app.cell
def _(mo, rainfall_months):
    rainfall_alt = __import__("altair")

    rainfall_scatter = (
        rainfall_alt.Chart(rainfall_months)
        .mark_circle(size=65)
        .encode(
            x=rainfall_alt.X(
                "gpm_standardized_anomaly:Q",
                title="GPM rainfall anomaly (z)"
            ),
            y=rainfall_alt.Y(
                "smap_standardized_anomaly:Q",
                title="SMAP soil-moisture anomaly (z)"
            ),
            tooltip=[
                rainfall_alt.Tooltip(
                    "date:T",
                    title="Month",
                    format="%Y-%m"
                ),
                rainfall_alt.Tooltip(
                    "gpm_standardized_anomaly:Q",
                    title="Rainfall z",
                    format=".2f"
                ),
                rainfall_alt.Tooltip(
                    "smap_standardized_anomaly:Q",
                    title="Soil moisture z",
                    format=".2f"
                ),
            ],
        )
        .properties(
            height=450,
            title="Same-month rainfall vs soil-moisture anomalies"
        )
        .interactive()
    )

    mo.ui.altair_chart(rainfall_scatter)
    return


@app.cell
def _(lag_results, mo):
    lag_alt = __import__("altair")

    lag_chart = (
        lag_alt.Chart(lag_results)
        .mark_line(point=True)
        .encode(
            x=lag_alt.X(
                "lag_months:Q",
                title="Rainfall lead (months)"
            ),
            y=lag_alt.Y(
                "pearson_r:Q",
                title="Pearson correlation"
            ),
            tooltip=[
                lag_alt.Tooltip(
                    "lag_months:Q",
                    title="Lag"
                ),
                lag_alt.Tooltip(
                    "pearson_r:Q",
                    title="Pearson r",
                    format=".3f"
                ),
                lag_alt.Tooltip(
                    "pearson_p:Q",
                    title="p-value",
                    format=".2e"
                ),
            ],
        )
        .properties(
            height=350,
            title="Rainfall–soil-moisture correlation by lag"
        )
        .interactive()
    )

    mo.ui.altair_chart(lag_chart)
    return


@app.cell
def _(lag_results, mo):
    lag_rows = lag_results[
        [
            "lag_months",
            "n",
            "pearson_r",
            "pearson_p",
            "spearman_rho",
            "spearman_p",
        ]
    ].copy()

    lag_rows["pearson_r"] = lag_rows[
        "pearson_r"
    ].round(3)

    lag_rows["spearman_rho"] = lag_rows[
        "spearman_rho"
    ].round(3)

    mo.ui.table(
        lag_rows,
        selection=None
    )
    return


@app.cell
def _(mo, trend):
    trend_result_166 = trend["state_trend"]

    slope_166 = float(trend_result_166["sen_slope_per_year"])
    tau_166 = float(trend_result_166["kendall_tau"])
    p_value_166 = float(trend_result_166["p_value"])
    significant_166 = bool(trend_result_166["significant_at_0_05"])
    trend_class_166 = trend_result_166["trend_class"]

    mo.md(
        f"""
        ## 📉 TREND TEST — Long-Term Soil Moisture

        | Metric | Result |
        |---|---:|
        | Sen slope / year | **{slope_166:.8f}** |
        | Kendall τ | **{tau_166:.6f}** |
        | p-value | **{p_value_166:.6f}** |
        | Significant at α = 0.05 | **{significant_166}** |
        | Trend classification | **{trend_class_166}** |

        ### Spatial result

        **0 of 984 SMAP cells** showed a statistically
        significant long-term trend.

        Seasonal spatial testing also produced
        **0 FDR-significant spatial-seasonal results**.

        **Interpretation:** the slightly negative Sen slope
        is not evidence of a statistically demonstrated
        long-term drying trend.
        """
    )
    return


@app.cell
def _(final_evidence, mo):
    final_claim_166 = final_evidence[
        "INTERPRETATION"
    ]["final_finding"]

    mo.md(
        f"""
        <div style="
            margin:32px 0;
            padding:28px;
            border:2px solid #222;
            border-radius:18px;
        ">

        <div style="
            font-size:14px;
            font-weight:700;
            letter-spacing:1px;
            margin-bottom:10px;
        ">
        🕵️ EARTH TREND DETECTIVE — FINAL VERDICT
        </div>

        <div style="
            font-size:26px;
            font-weight:700;
            line-height:1.35;
            margin-bottom:24px;
        ">
        {final_claim_166}
        </div>

        <div style="
            padding:18px;
            border:1px solid #ddd;
            border-radius:12px;
            margin-bottom:22px;
        ">

        ### 🔎 Evidence chain

        **01 — WHEN**

        **April 2015 → September 2026**  
        138 monthly periods across **984 SMAP cells**.

        **02 — WHERE**

        Rainfall–soil-moisture relationships were positive
        across all **984 mapped SMAP cells**.

        Mean spatial Pearson **r = 0.672**.

        **03 — EXTREMES**

        **6 dry** and **12 wet** event candidates were identified.

        The strongest wet event affected **941 of 984 cells**.

        **04 — RAINFALL LINK**

        Same-month standardized anomalies:

        **Pearson r = 0.714**

        Autocorrelation-aware adjusted:

        **p = 2.20 × 10⁻¹⁴**

        **05 — TREND**

        Long-term state-level trend:

        **p = 0.931**

        **0 of 984 SMAP cells** showed a significant
        first-pass long-term trend.

        </div>

        <div style="
            padding:18px;
            border:1px solid #ddd;
            border-radius:12px;
        ">

        ### 🔬 Scientific interpretation

        The evidence supports **rainfall-linked variability
        and episodic soil-moisture extremes**, rather than
        a simple state-wide long-term drying signal.

        </div>

        <div style="
            margin-top:18px;
            padding:14px 18px;
            border-radius:10px;
            border:1px solid #ddd;
            font-size:14px;
        ">

        ⚠️ **Scientific caution:** correlation does not establish
        causality. The long-term trend and spatial analyses also
        have the methodological limitations documented below.

        </div>

        </div>
        """
    )
    return


@app.cell
def _(mo):
    mo.md("""
    - The primary long-term trend test is a first-pass
      Kendall/Sen analysis and is not fully seasonality- and
      autocorrelation-corrected.
    - Seasonal trend testing is not a full autocorrelation-corrected
      Seasonal Mann-Kendall implementation.
    - Seasonal sample sizes are relatively small.
    - GPM and SMAP have different spatial resolutions.
    - Multiple SMAP cells can share one GPM cell, so spatial
      correlations are not 984 independent experiments.
    - FDR correction is a screening correction, not a complete
      spatial-dependence model.
    - Extreme-event thresholds are analytical definitions.
    - The GPM cross-variable period ends in September 2025,
      while SMAP continues through September 2026.
    - The analysis demonstrates association, not causality.
    """)
    return


@app.cell
def _(Path, mo):
    report_path = (
        Path(__file__).resolve().parent.parent
        / "reports"
        / "earthtrend_scientific_report.html"
    )

    if report_path.is_file():
        report_heading = mo.md(
            """
            ## 📄 Export Scientific Report

            Download the standalone HTML report with the saved evidence,
            scientific methodology, limitations, and embedded figures.
            """
        )
        report_download = mo.download(
            data=lambda: report_path.read_bytes(),
            filename="earthtrend_scientific_report.html",
            mimetype="text/html",
            label="Download Scientific Report",
        )
        report_ui = mo.vstack([report_heading, report_download])
    else:
        report_ui = mo.md(
            "### 📄 Scientific report not found. "
            "Generate it with `python scripts/export_scientific_report.py`."
        )

    report_ui
    return


if __name__ == "__main__":
    app.run()
