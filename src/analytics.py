import pandas as pd
import plotly.express as px
import streamlit as st
from src.email_engine import EmailEngine
from src.model import Contact, EmailLog, EmailTemplate
from src.database import fetch_all_jobs, get_all_templates


def get_colorscale(name):
    custom_scales = {
        "Salmon": [
            [0.0, "rgb(255, 229, 229)"],
            [0.5, "rgb(255, 160, 122)"],
            [1.0, "rgb(233, 87, 63)"],
        ],
        "Cool": [
            [0.0, "rgb(0, 255, 255)"],
            [0.5, "rgb(127, 127, 255)"],
            [1.0, "rgb(255, 0, 255)"],
        ],
        "Plasma": "plasma",
        "Sunset": "sunset",
        "Viridis": "viridis",
        "Inferno": "inferno",
        "Magma": "magma",
        "Turbo": "turbo",
        "cyan": [
            [0.0, "rgb(224, 255, 255)"],
            [0.5, "rgb(0, 255, 255)"],
            [1.0, "rgb(0, 139, 139)"],
        ],
    }
    return custom_scales.get(name, "viridis")


def plot_bar(df, x, y, title, color_col=None, orientation="v", color_map="Viridis"):
    return px.bar(
        df,
        x=x,
        y=y,
        title=title,
        color=color_col or y,
        orientation=orientation,
        color_continuous_scale=color_map,
    )


class JobAnalyticsEngine:
    def __init__(self, conn):
        self.conn = conn
        self.df = fetch_all_jobs(self.conn)
        self.filtered_df = pd.DataFrame()
        self.status_counts = pd.DataFrame()

    def apply_filters(self, status_filter, priority_filter, date_range):
        self.df["date_applied"] = pd.to_datetime(self.df["date_applied"])
        self.filtered_df = self.df[
            self.df["status"].isin(status_filter)
            & self.df["priority"].isin(priority_filter)
            & self.df["date_applied"].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]))
        ]
        self.status_counts = self.filtered_df["status"].value_counts().reset_index()
        self.status_counts.columns = ["Status", "Count"]

    def show_summary(self):
        st.markdown("### Summary Statistics")
        col1, col2 = st.columns(2)
        col1.metric("Total Applications", len(self.filtered_df))
        col2.metric("Unique Companies", self.filtered_df["company_name"].nunique())

    def show_insights(self):
        with st.expander("💡 Personalized Insights", expanded=True):
            for label, emoji in {
                "Offer Received": "🎉",
                "Interview Scheduled": "🗓️",
                "Ghosted": "👻",
                "Rejected": "💔",
            }.items():
                if label in self.status_counts["Status"].to_numpy():
                    count = self.status_counts.query(f"Status == '{label}'")["Count"].sum()
                    if count:
                        func = (
                            st.success
                            if label == "Offer Received"
                            else (st.info if label == "Interview Scheduled" else (st.warning if label == "Ghosted" else st.error))
                        )
                        func(f"{emoji} {count} {label}(s)")

    def show_status_priority(self):
        with st.expander("📌 Application Status & Priorities"):
            status_df = self.status_counts
            priority_df = self.filtered_df["priority"].value_counts().reset_index()
            priority_df.columns = ["Priority", "Count"]

            col1, col2 = st.columns(2)
            col1.plotly_chart(
                plot_bar(
                    status_df,
                    "Status",
                    "Count",
                    "Status Distribution",
                    color_map=get_colorscale("Turbo"),
                ),
                use_container_width=True,
            )
            col2.plotly_chart(
                plot_bar(
                    priority_df,
                    "Priority",
                    "Count",
                    "Priority Distribution",
                    color_map=get_colorscale("Magma"),
                ),
                use_container_width=True,
            )

    def show_timeline(self):
        with st.expander("📅 Timeline Analysis"):
            trend = (
                self.filtered_df.groupby(self.filtered_df["date_applied"].dt.to_period("M"))
                .size()
                .reset_index(name="Applications")
            )
            trend["date_applied"] = trend["date_applied"].astype(str)
            st.plotly_chart(
                px.line(
                    trend,
                    x="date_applied",
                    y="Applications",
                    title="Applications Over Time",
                    markers=True,
                ),
                use_container_width=True,
            )

    def show_followups(self):
        with st.expander("⏱️ Follow-up Metrics"):
            self.filtered_df["follow_up_date"] = pd.to_datetime(self.filtered_df["follow_up_date"], errors="coerce")
            self.filtered_df["time_to_follow_up"] = (
                self.filtered_df["follow_up_date"] - self.filtered_df["date_applied"]
            ).dt.days
            followup = (
                self.filtered_df.dropna(subset=["time_to_follow_up"]).groupby("status")["time_to_follow_up"].mean().reset_index()
            )
            st.plotly_chart(
                plot_bar(
                    followup,
                    "status",
                    "time_to_follow_up",
                    "Avg Days to Follow-up by Status",
                    color_map=get_colorscale("Salmon"),
                ),
                use_container_width=True,
            )

    def show_top_targets(self):
        with st.expander("🏢 Top Applications Targets"):
            col1, col2 = st.columns(2)
            company_df = self.filtered_df["company_name"].value_counts().head(10).reset_index(name="Count")
            company_df.columns = ["Company", "Count"]
            job_df = self.filtered_df["job_title"].value_counts().head(10).reset_index(name="Count")
            job_df.columns = ["Job Title", "Count"]

            col1.plotly_chart(
                plot_bar(
                    company_df,
                    "Count",
                    "Company",
                    "Top 10 Companies",
                    orientation="h",
                    color_map=get_colorscale("Cool"),
                ),
                use_container_width=True,
            )
            col2.plotly_chart(
                plot_bar(
                    job_df,
                    "Count",
                    "Job Title",
                    "Top 10 Job Titles",
                    orientation="h",
                    color_map=get_colorscale("Plasma"),
                ),
                use_container_width=True,
            )

    def show_conversion(self):
        with st.expander("🌡️ Conversion & Ghosting Rate"):
            conversion_df = self.status_counts.copy()
            conversion_df["Conversion Rate (%)"] = (conversion_df["Count"] / len(self.filtered_df)) * 100
            st.plotly_chart(
                plot_bar(
                    conversion_df,
                    "Status",
                    "Conversion Rate (%)",
                    "Conversion Rate by Status",
                    color_map=get_colorscale("Cyan"),
                ),
                use_container_width=True,
            )

    def show_heatmap(self):
        with st.expander("📅 Heatmap of Applications"):
            heatmap = self.filtered_df.copy()
            heatmap["month_applied"] = heatmap["date_applied"].dt.to_period("M").astype(str)
            pivot = heatmap.pivot_table(
                index="month_applied",
                columns="status",
                aggfunc="size",
                fill_value=0,
            ).T
            st.plotly_chart(
                px.imshow(
                    pivot,
                    aspect="auto",
                    title="Monthly Status Heatmap",
                    color_continuous_scale="YlGnBu",
                ),
                use_container_width=True,
            )

    def show_reminders(self):
        with st.expander("🔔 Follow-up Reminders & Recents"):
            today = pd.to_datetime("today").normalize()
            self.filtered_df["follow_up_date"] = pd.to_datetime(self.filtered_df["follow_up_date"], errors="coerce")
            upcoming = self.filtered_df[self.filtered_df["follow_up_date"] >= today]
            recent = self.filtered_df.sort_values(by="date_applied", ascending=False).head(5)

            col1, col2 = st.columns(2)
            col1.markdown("**📬 Upcoming Follow-ups**")
            (
                col1.dataframe(
                    upcoming[
                        [
                            "company_name",
                            "job_title",
                            "follow_up_date",
                            "notes",
                        ]
                    ]
                )
                if not upcoming.empty
                else col1.write("No upcoming follow-ups.")
            )

            col2.markdown("**🕑 Recent Applications**")
            col2.dataframe(recent[["company_name", "job_title", "date_applied", "status"]])


def analytics_ui(conn):
    st.subheader("📊 Analytics Dashbaord")

    engine = JobAnalyticsEngine(conn)

    if engine.df.empty:
        st.warning("No applications yet! Add some to see insights.")
        return

    st.sidebar.header("🧮 Filter Options")
    status_filter = st.sidebar.multiselect(
        "Select Status",
        engine.df["status"].unique(),
        default=list(engine.df["status"].unique()),
    )
    priority_filter = st.sidebar.multiselect(
        "Select Priority",
        engine.df["priority"].unique(),
        default=list(engine.df["priority"].unique()),
    )
    date_range = st.sidebar.date_input(
        "Select Date Range",
        [engine.df["date_applied"].min(), engine.df["date_applied"].max()],
    )

    engine.apply_filters(status_filter, priority_filter, date_range)

    if engine.filtered_df.empty:
        st.warning("No data available for the selected filters.")
        return

    engine.show_summary()
    engine.show_insights()
    engine.show_status_priority()
    engine.show_reminders()
    engine.show_timeline()
    engine.show_followups()
    engine.show_top_targets()
    engine.show_conversion()
    engine.show_heatmap()


def response_tracking_ui(session):
    """Track email response rates and effectiveness"""
    st.subheader("📈 Outreach Effectiveness")
    
    # Get email logs with contact/join data
    logs = session.query(EmailLog).order_by(EmailLog.sent_at.desc()).limit(100).all()
    
    if not logs:
        st.info("Send some emails first to see response analytics!")
        return
    
    # Calculate metrics
    total_sent = len([l for l in logs if l.status == "sent"])
    replied_contacts = session.query(Contact).filter_by(replied=True).count()
    response_rate = (replied_contacts / total_sent * 100) if total_sent > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📧 Emails Sent (30d)", total_sent)
    col2.metric("✅ Replies Received", replied_contacts)
    col3.metric("📊 Response Rate", f"{response_rate:.1f}%")
    
    # Template effectiveness
    st.markdown("### 📧 Template Effectiveness")
    templates = get_all_templates(session)
    effectiveness = []
    
    for template in templates:
        sent_count = session.query(EmailLog).filter_by(template_id=template.id, status="sent").count()
        if sent_count > 0:
            # Get contacts who received this template
            contact_ids = [l.contact_id for l in session.query(EmailLog).filter_by(template_id=template.id)]
            replied_count = session.query(Contact).filter(
                Contact.id.in_(contact_ids),
                Contact.replied == True
            ).count()
            
            effectiveness.append({
                "Template": template.name,
                "Sent": sent_count,
                "Replied": replied_count,
                "Rate": f"{(replied_count/sent_count*100):.1f}%"
            })
    
    if effectiveness:
        st.dataframe(effectiveness)
    
    # Recent activity timeline
    st.markdown("### 📅 Recent Activity")
    activity = []
    for log in logs[:20]:
        contact = session.query(Contact).get(log.contact_id)
        activity.append({
            "When": log.sent_at.strftime("%Y-%m-%d %H:%M"),
            "Contact": contact.name if contact else "Unknown",
            "Company": contact.company_name if contact else "",
            "Template": session.query(EmailTemplate).get(log.template_id).name if log.template_id else "Manual",
            "Status": "✅ Replied" if (contact and contact.replied) else "⏳ Pending"
        })
    
    st.dataframe(activity)
    
    # One-click reply marking
    st.markdown("### ✅ Mark as Replied")
    contacts_needing_reply = session.query(Contact).filter_by(replied=False, needs_followup=True).all()
    
    if contacts_needing_reply:
        contact_options = [f"{c.name} - {c.company_name}" for c in contacts_needing_reply]
        selected_idx = st.selectbox("Select contact who replied", range(len(contact_options)), 
                                   format_func=lambda x: contact_options[x])
        
        reply_notes = st.text_area("Reply details (optional)", placeholder="E.g., 'Scheduled interview for Friday'")
        
        if st.button("✅ Mark as Replied", type="primary"):
            contact_id = contacts_needing_reply[selected_idx].id
            engine = EmailEngine(session)
            if engine.mark_as_replied(contact_id, reply_notes):
                st.success("Contact marked as replied! Removed from follow-up list.")
                st.rerun()
    else:
        st.success("✅ All contacts have replied or are up-to-date!")