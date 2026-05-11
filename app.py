import json

import pandas as pd
import plotly.express as px
import streamlit as st


PAID_STATUSES = {"CONFIRMED", "PAID"}
FAILED_STATUSES = {"PAYMENT_FAILED", "FAILED"}
WAITLIST_STATUSES = {"WAITLISTED"}


st.set_page_config(
    page_title="Course Enrollment Dashboard",
    page_icon="🎓",
    layout="wide",
)


def apply_custom_styles() -> None:
    st.markdown(
        """
        <style>
        .main {background-color: #f8fafc;}
        .kpi-card {
            background: white;
            padding: 16px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.06);
            border-left: 6px solid #2563eb;
        }
        .kpi-title {font-size: 0.9rem; color: #475569; margin-bottom: 6px;}
        .kpi-value {font-size: 1.5rem; font-weight: 700; color: #0f172a;}
        .section-title {font-size: 1.25rem; font-weight: 700; margin-top: 8px;}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data
def load_enrollment_report(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "course_id" not in df.columns:
        raise ValueError("`enrollment_report.csv` must include `course_id`.")
    if "status" not in df.columns:
        raise ValueError("`enrollment_report.csv` must include `status`.")
    if "student_id" not in df.columns:
        df["student_id"] = ""
    df["status"] = df["status"].astype(str).str.upper().str.strip()
    return df


@st.cache_data
def load_course_summary(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as file:
        raw = json.load(file)
    rows = []
    for course_id, details in raw.items():
        rows.append(
            {
                "course_id": course_id,
                "course_name": details.get("course_name", ""),
                "capacity": int(details.get("capacity", 0)),
                "enrolled": int(details.get("enrolled", 0)),
                "remaining_seats": int(details.get("remaining_seats", 0)),
                "revenue": float(details.get("revenue", 0)),
            }
        )
    return pd.DataFrame(rows)


def enrich_enrollments(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["payment_status"] = data["status"].apply(
        lambda s: "PAID"
        if s in PAID_STATUSES
        else "FAILED"
        if s in FAILED_STATUSES
        else "WAITLISTED"
        if s in WAITLIST_STATUSES
        else "OTHER"
    )
    if "enrollment_date" in data.columns:
        data["enrollment_date"] = pd.to_datetime(data["enrollment_date"], errors="coerce")
    return data


def kpi_card(title: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def build_sidebar_filters(enrollment_df: pd.DataFrame, course_df: pd.DataFrame):
    st.sidebar.header("🔎 Global Filters")

    course_options = sorted(course_df["course_id"].tolist())
    selected_courses = st.sidebar.multiselect(
        "Course ID",
        options=course_options,
        default=course_options,
    )

    status_options = sorted(enrollment_df["status"].dropna().unique().tolist())
    selected_statuses = st.sidebar.multiselect(
        "Enrollment Status",
        options=status_options,
        default=status_options,
    )

    payment_options = sorted(enrollment_df["payment_status"].dropna().unique().tolist())
    selected_payment = st.sidebar.multiselect(
        "Payment Status",
        options=payment_options,
        default=payment_options,
    )

    return selected_courses, selected_statuses, selected_payment


def apply_filters(
    enrollment_df: pd.DataFrame,
    selected_courses,
    selected_statuses,
    selected_payment,
) -> pd.DataFrame:
    filtered = enrollment_df.copy()
    filtered = filtered[filtered["course_id"].isin(selected_courses)]
    filtered = filtered[filtered["status"].isin(selected_statuses)]
    filtered = filtered[filtered["payment_status"].isin(selected_payment)]

    return filtered


def show_top_kpis(enrollment_df: pd.DataFrame, course_df: pd.DataFrame) -> None:
    total_courses = int(course_df["course_id"].nunique())
    total_enrollments = int(len(enrollment_df))
    paid_enrollments = int((enrollment_df["status"].isin(PAID_STATUSES)).sum())
    failed_enrollments = int((enrollment_df["status"].isin(FAILED_STATUSES)).sum())
    waitlisted_students = int((enrollment_df["status"].isin(WAITLIST_STATUSES)).sum())
    total_revenue = float(course_df["revenue"].sum())

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        kpi_card("📚 Total Courses", f"{total_courses}")
    with col2:
        kpi_card("👨‍🎓 Total Enrollments", f"{total_enrollments}")
    with col3:
        kpi_card("✅ Paid Enrollments", f"{paid_enrollments}")
    with col4:
        kpi_card("❌ Failed Enrollments", f"{failed_enrollments}")
    with col5:
        kpi_card("🕒 Waitlisted", f"{waitlisted_students}")
    with col6:
        kpi_card("💰 Total Revenue", f"Rs. {total_revenue:,.0f}")


def show_course_search_section(enrollment_df: pd.DataFrame, course_df: pd.DataFrame) -> None:
    st.markdown("### 📚 Course Search & Filter")
    options = (
        course_df["course_id"].astype(str) + " - " + course_df["course_name"].astype(str)
    ).tolist()

    selected = st.selectbox("Search / Select Course", options=[""] + options)
    if not selected:
        st.info("Select a course to see details.")
        return

    selected_id = selected.split(" - ")[0]
    course_row = course_df[course_df["course_id"] == selected_id]
    if course_row.empty:
        st.warning("No course record found for the selected value.")
        return

    row = course_row.iloc[0]
    waitlisted = int(
        (
            (enrollment_df["course_id"] == selected_id)
            & (enrollment_df["status"].isin(WAITLIST_STATUSES))
        ).sum()
    )
    course_col1, course_col2, course_col3 = st.columns(3)
    with course_col1:
        st.metric("Course ID", row["course_id"])
        st.metric("Course Name", row["course_name"])
    with course_col2:
        st.metric("Capacity", int(row["capacity"]))
        st.metric("Enrolled Students", int(row["enrolled"]))
    with course_col3:
        st.metric("Remaining Seats", int(row["remaining_seats"]))
        st.metric("Waitlisted Students", waitlisted)
    st.metric("Revenue Generated", f"Rs. {float(row['revenue']):,.0f}")


def show_enrollment_insights(enrollment_df: pd.DataFrame) -> None:
    st.markdown("### 👨‍🎓 Enrollment Insights")
    status_count = enrollment_df["status"].value_counts().reset_index()
    status_count.columns = ["status", "count"]

    colors = {
        "CONFIRMED": "#16a34a",
        "PAID": "#16a34a",
        "PAYMENT_FAILED": "#dc2626",
        "FAILED": "#dc2626",
        "WAITLISTED": "#f59e0b",
        "INVALID_COURSE": "#64748b",
        "INVALID_DATE": "#64748b",
    }

    col1, col2 = st.columns(2)
    with col1:
        bar_fig = px.bar(
            status_count,
            x="status",
            y="count",
            color="status",
            color_discrete_map=colors,
            title="Enrollment Status Count",
        )
        bar_fig.update_layout(showlegend=False)
        st.plotly_chart(bar_fig, use_container_width=True)
    with col2:
        pie_fig = px.pie(
            status_count,
            names="status",
            values="count",
            color="status",
            color_discrete_map=colors,
            title="Enrollment Status Distribution",
            hole=0.35,
        )
        st.plotly_chart(pie_fig, use_container_width=True)

    popular = (
        enrollment_df[enrollment_df["status"].isin(PAID_STATUSES)]
        .groupby("course_id")
        .size()
        .sort_values(ascending=False)
        .head(3)
    )
    waitlist = (
        enrollment_df[enrollment_df["status"].isin(WAITLIST_STATUSES)]
        .groupby("course_id")
        .size()
        .sort_values(ascending=False)
        .head(3)
    )
    info1, info2 = st.columns(2)
    with info1:
        st.write("**🔥 Most Popular Courses**")
        if popular.empty:
            st.info("No paid/confirmed enrollments in current filter.")
        else:
            st.dataframe(popular.rename("paid_enrollments").reset_index(), use_container_width=True)
    with info2:
        st.write("**🕒 Highest Waitlist Courses**")
        if waitlist.empty:
            st.info("No waitlisted enrollments in current filter.")
        else:
            st.dataframe(waitlist.rename("waitlisted").reset_index(), use_container_width=True)


def show_revenue_analysis(enrollment_df: pd.DataFrame, course_df: pd.DataFrame) -> None:
    st.markdown("### 💰 Revenue Analysis")

    revenue_fig = px.bar(
        course_df.sort_values("revenue", ascending=False),
        x="course_id",
        y="revenue",
        color="revenue",
        title="Revenue Per Course",
        text_auto=True,
    )
    st.plotly_chart(revenue_fig, use_container_width=True)

    if "enrollment_date" in enrollment_df.columns and enrollment_df["enrollment_date"].notna().any():
        paid = enrollment_df[enrollment_df["status"].isin(PAID_STATUSES)].copy()
        merged = paid.merge(
            course_df[["course_id", "revenue"]],
            on="course_id",
            how="left",
        )
        trend = (
            merged.groupby(merged["enrollment_date"].dt.date)["revenue"]
            .sum()
            .reset_index()
            .rename(columns={"enrollment_date": "date"})
        )
        line_fig = px.line(trend, x="date", y="revenue", markers=True, title="Revenue Trend Over Time")
        st.plotly_chart(line_fig, use_container_width=True)
    else:
        st.info("Revenue trend unavailable: `enrollment_date` is not present in report data.")

    high_rev = course_df.sort_values("revenue", ascending=False).head(3)
    low_enroll = course_df.sort_values("enrolled", ascending=True).head(3)
    c1, c2 = st.columns(2)
    with c1:
        st.write("**🏆 Highest Revenue Courses**")
        st.dataframe(high_rev[["course_id", "course_name", "revenue"]], use_container_width=True)
    with c2:
        st.write("**📉 Low Enrollment Courses**")
        st.dataframe(low_enroll[["course_id", "course_name", "enrolled"]], use_container_width=True)


def show_seat_allocation(course_df: pd.DataFrame) -> None:
    st.markdown("### 🪑 Seat Allocation Analysis")
    seat_df = course_df.copy()
    seat_df["utilization_pct"] = (seat_df["enrolled"] / seat_df["capacity"] * 100).round(2)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Seats", int(seat_df["capacity"].sum()))
    with col2:
        st.metric("Filled Seats", int(seat_df["enrolled"].sum()))
    with col3:
        st.metric("Remaining Seats", int(seat_df["remaining_seats"].sum()))

    util_fig = px.bar(
        seat_df.sort_values("utilization_pct", ascending=False),
        x="course_id",
        y="utilization_pct",
        color="utilization_pct",
        title="Capacity Utilization (%)",
        text_auto=True,
    )
    st.plotly_chart(util_fig, use_container_width=True)

    full_courses = seat_df[seat_df["remaining_seats"] <= 0]
    near_capacity = seat_df[(seat_df["remaining_seats"] > 0) & (seat_df["utilization_pct"] >= 80)]

    c1, c2 = st.columns(2)
    with c1:
        st.write("**🚨 Full Courses**")
        if full_courses.empty:
            st.success("No courses are fully occupied.")
        else:
            st.dataframe(full_courses[["course_id", "course_name", "capacity", "enrolled"]], use_container_width=True)
    with c2:
        st.write("**⚠️ Near Capacity (80%+)**")
        if near_capacity.empty:
            st.success("No courses are near full capacity.")
        else:
            st.dataframe(
                near_capacity[["course_id", "course_name", "utilization_pct", "remaining_seats"]],
                use_container_width=True,
            )


def show_data_tables(enrollment_df: pd.DataFrame, course_df: pd.DataFrame) -> None:
    st.markdown("### 📋 Data Tables")
    st.write("**Enrollment Report**")
    st.dataframe(enrollment_df, use_container_width=True)
    st.write("**Course Summary**")
    st.dataframe(course_df, use_container_width=True)

    st.markdown("### 📥 Download Data")
    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            label="Download Filtered Enrollment Report (CSV)",
            data=to_csv_bytes(enrollment_df),
            file_name="filtered_enrollment_report.csv",
            mime="text/csv",
        )
    with d2:
        revenue_summary = course_df[["course_id", "course_name", "revenue"]].sort_values(
            "revenue", ascending=False
        )
        st.download_button(
            label="Download Revenue Summary (CSV)",
            data=to_csv_bytes(revenue_summary),
            file_name="revenue_summary.csv",
            mime="text/csv",
        )


def show_summary_insights(enrollment_df: pd.DataFrame, course_df: pd.DataFrame) -> None:
    st.markdown("### 📈 Summary Insights")
    total_revenue = float(course_df["revenue"].sum())
    avg_enrollment = float(course_df["enrolled"].mean()) if not course_df.empty else 0
    overall_util = (
        (course_df["enrolled"].sum() / course_df["capacity"].sum()) * 100
        if course_df["capacity"].sum() > 0
        else 0
    )
    waitlist_pct = (
        (enrollment_df["status"].isin(WAITLIST_STATUSES).sum() / len(enrollment_df)) * 100
        if len(enrollment_df) > 0
        else 0
    )

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("Total Revenue", f"Rs. {total_revenue:,.0f}")
    with s2:
        st.metric("Avg Enrollment / Course", f"{avg_enrollment:.2f}")
    with s3:
        st.metric("Overall Seat Utilization", f"{overall_util:.2f}%")
    with s4:
        st.metric("Waitlist Percentage", f"{waitlist_pct:.2f}%")

    st.markdown("### ⚙️ Alerts")
    failed_spike = (
        enrollment_df[enrollment_df["status"].isin(FAILED_STATUSES)]
        .groupby("course_id")
        .size()
        .sort_values(ascending=False)
    )
    if not failed_spike.empty and failed_spike.iloc[0] >= 2:
        st.warning(
            f"High failed payment spike detected in `{failed_spike.index[0]}` "
            f"({int(failed_spike.iloc[0])} failed records)."
        )
    else:
        st.info("No major failed payment spikes detected in the current filtered data.")


def main() -> None:
    apply_custom_styles()
    st.title("🎓 Course Enrollment & Revenue Dashboard")
    st.caption("Interactive analytics portal for enrollments, revenue, payment outcomes, and seat utilization.")

    enrollment_path = "enrollment_report.csv"
    summary_path = "course_summary.json"

    try:
        enrollment_df = load_enrollment_report(enrollment_path)
        course_df = load_course_summary(summary_path)
    except FileNotFoundError as error:
        st.error(f"Data file missing: {error}")
        st.stop()
    except ValueError as error:
        st.error(str(error))
        st.stop()

    enrollment_df = enrich_enrollments(enrollment_df)

    section = st.sidebar.radio(
        "🧭 Navigate",
        [
            "Overview",
            "Course Search",
            "Enrollment Insights",
            "Revenue Analysis",
            "Seat Allocation",
            "Data Tables & Download",
            "Summary Insights",
        ],
    )

    selected_courses, selected_statuses, selected_payment = build_sidebar_filters(
        enrollment_df,
        course_df,
    )
    filtered_enrollment = apply_filters(
        enrollment_df,
        selected_courses,
        selected_statuses,
        selected_payment,
    )
    filtered_course = course_df[course_df["course_id"].isin(selected_courses)].copy()

    show_top_kpis(filtered_enrollment, filtered_course)

    if filtered_enrollment.empty:
        st.warning("No records found for selected filters. Please adjust filter criteria.")
        st.stop()

    if section == "Overview":
        show_enrollment_insights(filtered_enrollment)
        show_revenue_analysis(filtered_enrollment, filtered_course)
    elif section == "Course Search":
        show_course_search_section(filtered_enrollment, filtered_course)
    elif section == "Enrollment Insights":
        show_enrollment_insights(filtered_enrollment)
    elif section == "Revenue Analysis":
        show_revenue_analysis(filtered_enrollment, filtered_course)
    elif section == "Seat Allocation":
        show_seat_allocation(filtered_course)
    elif section == "Data Tables & Download":
        show_data_tables(filtered_enrollment, filtered_course)
    elif section == "Summary Insights":
        show_summary_insights(filtered_enrollment, filtered_course)


if __name__ == "__main__":
    main()
