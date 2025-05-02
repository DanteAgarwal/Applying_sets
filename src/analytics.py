# import streamlit as st
# import pandas as pd
# import plotly.express as px
# from database import fetch_all_jobs

# def analytics_ui(conn):
#     st.subheader("📊 Job Application Insights")

#     # Fetch data
#     df = fetch_all_jobs(conn)
#     if df.empty:
#         st.warning("No applications yet! Add some to see insights.")
#         return

#     # Sidebar for filters
#     st.sidebar.header("Filter Options")
#     status_filter = st.sidebar.multiselect("Select Status", df['status'].unique(), default=df['status'].unique())
#     priority_filter = st.sidebar.multiselect("Select Priority", df['priority'].unique(), default=df['priority'].unique())
#     date_range = st.sidebar.date_input("Select Date Range", [df['date_applied'].min(), df['date_applied'].max()])

#     # Apply filters
#     filtered_df = df[
#         (df['status'].isin(status_filter)) &
#         (df['priority'].isin(priority_filter)) &
#         (pd.to_datetime(df['date_applied']).between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])))
#     ]

#     if filtered_df.empty:
#         st.warning("No data available for the selected filters.")
#         return

#     # Summary Statistics
#     st.markdown("### Summary Statistics")
#     total_applications = len(filtered_df)
#     interviews_scheduled = filtered_df[filtered_df['status'] == 'Interview Scheduled'].shape[0]
#     offers_received = filtered_df[filtered_df['status'] == 'Offer Received'].shape[0]
#     rejections = filtered_df[filtered_df['status'] == 'Rejected'].shape[0]
#     ghosted = filtered_df[filtered_df['status'] == 'Ghosted'].shape[0]

#     col1, col2, col3, col4, col5 = st.columns(5)
#     col1.metric("Total Applications", total_applications)
#     col2.metric("Interviews Scheduled", interviews_scheduled)
#     col3.metric("Offers Received", offers_received)
#     col4.metric("Rejections", rejections)
#     col5.metric("Ghosted", ghosted)

#      # Personalized Insights
#     st.markdown("### Personalized Insights")
#     if not filtered_df.empty:
#         st.write("Here are some personalized insights based on your application data:")
#         if offers_received > 0:
#             st.success(f"Congratulations! You have received {offers_received} offers.")
#         if interviews_scheduled > 0:
#             st.info(f"You have {interviews_scheduled} interviews scheduled. Prepare well!")
#         if rejections > 0:
#             st.warning(f"You have been rejected {rejections} times. Keep improving!")
#         if ghosted > 0:
#             st.warning(f"You have been ghosted {ghosted} times. Consider following up.")


#     # Status Breakdown
#     st.markdown("### Application Status Breakdown")
#     status_counts = filtered_df['status'].value_counts().reset_index()
#     status_counts.columns = ['Status', 'Count']

#     fig = px.pie(status_counts, values='Count', names='Status', title='Application Status Distribution', hole=0.5)
#     st.plotly_chart(fig)

#     # Priority Breakdown
#     st.markdown("### Priority Breakdown")
#     priority_counts = filtered_df['priority'].value_counts().reset_index()
#     priority_counts.columns = ['Priority', 'Count']

#     fig = px.pie(priority_counts, values='Count', names='Priority', title='Priority Distribution', hole=0.5)
#     st.plotly_chart(fig)

#     # Applications Over Time
#     st.markdown("### Applications Over Time")
#     filtered_df['date_applied'] = pd.to_datetime(filtered_df['date_applied'])
#     applications_over_time = filtered_df.groupby(filtered_df['date_applied'].dt.to_period('M')).size().reset_index(name='Count')
#     applications_over_time['date_applied'] = applications_over_time['date_applied'].astype(str)

#     fig = px.line(applications_over_time, x='date_applied', y='Count', title='Applications Over Time',
# labels={'Count': 'Number of Applications', 'date_applied': 'Month'})
#     st.plotly_chart(fig)

#     # Average Time to Follow-up
#     st.markdown("### Average Time to Follow-up")
#     filtered_df['follow_up_date'] = pd.to_datetime(filtered_df['follow_up_date'])
#     filtered_df['time_to_follow_up'] = (filtered_df['follow_up_date'] - filtered_df['date_applied']).dt.days
#     avg_time_to_follow_up = filtered_df.groupby('status')['time_to_follow_up'].mean().reset_index()
#     fig = px.bar(avg_time_to_follow_up, x='status', y='time_to_follow_up',
# title='Average Time to Follow-up by Status',
# labels={'time_to_follow_up': 'Average Days to Follow-up', 'status': 'Status'},
# color='time_to_follow_up', color_continuous_scale='Viridis')
#     st.plotly_chart(fig)

#     # Most Applied Companies and Job Titles
#     st.markdown("### Most Applied Companies and Job Titles")
#     company_counts = filtered_df['company_name'].value_counts().head(5).reset_index(name='Count')
#     company_counts.columns = ['Company', 'Count']

#     job_title_counts = filtered_df['job_title'].value_counts().head(5).reset_index(name='Count')
#     job_title_counts.columns = ['Job Title', 'Count']

#     col1, col2 = st.columns(2)
#     with col1:
#         fig = px.bar(company_counts, x='Count', y='Company', orientation='h', title='Top 5 Companies Applied To', color='Count',
#  color_continuous_scale='Blues')
#         st.plotly_chart(fig)

#     with col2:
#         fig = px.bar(job_title_counts,
#  x='Count', y='Job Title', orientation='h',
#  title='Top 5 Job Titles Applied To', color='Count',
# color_continuous_scale='Greens')
#         st.plotly_chart(fig)

#     # Conversion Rates
#     st.markdown("### Conversion Rates")
#     conversion_rates = filtered_df.groupby('status').size().reset_index(name='Count')
#     conversion_rates['Conversion Rate (%)'] = (conversion_rates['Count'] / len(filtered_df)) * 100

#     fig = px.bar(conversion_rates, x='status',
#     y='Conversion Rate (%)', title='Conversion Rates by Status',
#     labels={'Conversion Rate (%)': 'Conversion Rate (%)', 'status': 'Status'},
#     color='Conversion Rate (%)', color_continuous_scale='Viridis')
#     st.plotly_chart(fig)

#     # Follow-up Reminders
#     st.markdown("### Follow-up Reminders")
#     today = pd.to_datetime('today').normalize()
#     upcoming_follow_ups = filtered_df[filtered_df['follow_up_date'] >= today]

#     if not upcoming_follow_ups.empty:
#         st.write("Here are your upcoming follow-ups:")
#         st.dataframe(upcoming_follow_ups[['company_name', 'job_title', 'follow_up_date', 'notes']])
#     else:
#         st.write("No upcoming follow-ups.")

import pandas as pd
import plotly.express as px
import streamlit as st

from src.database import fetch_all_jobs


def get_colorscale(name):
    custom_scales = {
        'Salmon': [
            [0.0, 'rgb(255, 229, 229)'],
            [0.5, 'rgb(255, 160, 122)'],
            [1.0, 'rgb(233, 87, 63)'],
        ],
        'Cool': [
            [0.0, 'rgb(0, 255, 255)'],
            [0.5, 'rgb(127, 127, 255)'],
            [1.0, 'rgb(255, 0, 255)'],
        ],
        'Plasma': 'plasma',
        'Sunset': 'sunset',
        'Viridis': 'viridis',
        'Inferno': 'inferno',
        'Magma': 'magma',
        'Turbo': 'turbo',
        'cyan': [
            [0.0, 'rgb(224, 255, 255)'],
            [0.5, 'rgb(0, 255, 255)'],
            [1.0, 'rgb(0, 139, 139)'],
        ],
    }
    return custom_scales.get(name, 'viridis')


def plot_bar(df, x, y, title, color_col=None, orientation='v', color_map='Viridis'):
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
        self.df['date_applied'] = pd.to_datetime(self.df['date_applied'])
        self.filtered_df = self.df[
            self.df['status'].isin(status_filter)
            & self.df['priority'].isin(priority_filter)
            & self.df['date_applied'].between(
                pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            )
        ]
        self.status_counts = self.filtered_df['status'].value_counts().reset_index()
        self.status_counts.columns = ['Status', 'Count']

    def show_summary(self):
        st.markdown("### Summary Statistics")
        col1, col2 = st.columns(2)
        col1.metric("Total Applications", len(self.filtered_df))
        col2.metric("Unique Companies", self.filtered_df['company_name'].nunique())

    def show_insights(self):
        with st.expander("💡 Personalized Insights", expanded=True):
            for label, emoji in {
                'Offer Received': '🎉',
                'Interview Scheduled': '🗓️',
                'Ghosted': '👻',
                'Rejected': '💔',
            }.items():
                if label in self.status_counts['Status'].values:
                    count = self.status_counts.query(f"Status == '{label}'")[
                        'Count'
                    ].sum()
                    if count:
                        func = (
                            st.success
                            if label == 'Offer Received'
                            else (
                                st.info
                                if label == 'Interview Scheduled'
                                else (st.warning if label == 'Ghosted' else st.error)
                            )
                        )
                        func(f"{emoji} {count} {label}(s)")

    def show_status_priority(self):
        with st.expander("📌 Application Status & Priorities"):
            status_df = self.status_counts
            priority_df = self.filtered_df['priority'].value_counts().reset_index()
            priority_df.columns = ['Priority', 'Count']

            col1, col2 = st.columns(2)
            col1.plotly_chart(
                plot_bar(
                    status_df,
                    'Status',
                    'Count',
                    'Status Distribution',
                    color_map=get_colorscale('Turbo'),
                ),
                use_container_width=True,
            )
            col2.plotly_chart(
                plot_bar(
                    priority_df,
                    'Priority',
                    'Count',
                    'Priority Distribution',
                    color_map=get_colorscale('Magma'),
                ),
                use_container_width=True,
            )

    def show_timeline(self):
        with st.expander("📅 Timeline Analysis"):
            trend = (
                self.filtered_df.groupby(
                    self.filtered_df['date_applied'].dt.to_period('M')
                )
                .size()
                .reset_index(name='Applications')
            )
            trend['date_applied'] = trend['date_applied'].astype(str)
            st.plotly_chart(
                px.line(
                    trend,
                    x='date_applied',
                    y='Applications',
                    title='Applications Over Time',
                    markers=True,
                ),
                use_container_width=True,
            )

    def show_followups(self):
        with st.expander("⏱️ Follow-up Metrics"):
            self.filtered_df['follow_up_date'] = pd.to_datetime(
                self.filtered_df['follow_up_date'], errors='coerce'
            )
            self.filtered_df['time_to_follow_up'] = (
                self.filtered_df['follow_up_date'] - self.filtered_df['date_applied']
            ).dt.days
            followup = (
                self.filtered_df.dropna(subset=['time_to_follow_up'])
                .groupby('status')['time_to_follow_up']
                .mean()
                .reset_index()
            )
            st.plotly_chart(
                plot_bar(
                    followup,
                    'status',
                    'time_to_follow_up',
                    'Avg Days to Follow-up by Status',
                    color_map=get_colorscale('Salmon'),
                ),
                use_container_width=True,
            )

    def show_top_targets(self):
        with st.expander("🏢 Top Applications Targets"):
            col1, col2 = st.columns(2)
            company_df = (
                self.filtered_df['company_name']
                .value_counts()
                .head(10)
                .reset_index(name='Count')
            )
            company_df.columns = ['Company', 'Count']
            job_df = (
                self.filtered_df['job_title']
                .value_counts()
                .head(10)
                .reset_index(name='Count')
            )
            job_df.columns = ['Job Title', 'Count']

            col1.plotly_chart(
                plot_bar(
                    company_df,
                    'Count',
                    'Company',
                    'Top 10 Companies',
                    orientation='h',
                    color_map=get_colorscale('Cool'),
                ),
                use_container_width=True,
            )
            col2.plotly_chart(
                plot_bar(
                    job_df,
                    'Count',
                    'Job Title',
                    'Top 10 Job Titles',
                    orientation='h',
                    color_map=get_colorscale('Plasma'),
                ),
                use_container_width=True,
            )

    def show_conversion(self):
        with st.expander("🌡️ Conversion & Ghosting Rate"):
            conversion_df = self.status_counts.copy()
            conversion_df['Conversion Rate (%)'] = (
                conversion_df['Count'] / len(self.filtered_df)
            ) * 100
            st.plotly_chart(
                plot_bar(
                    conversion_df,
                    'Status',
                    'Conversion Rate (%)',
                    'Conversion Rate by Status',
                    color_map=get_colorscale('Cyan'),
                ),
                use_container_width=True,
            )

    def show_heatmap(self):
        with st.expander("📅 Heatmap of Applications"):
            heatmap = self.filtered_df.copy()
            heatmap['month_applied'] = (
                heatmap['date_applied'].dt.to_period('M').astype(str)
            )
            pivot = heatmap.pivot_table(
                index='month_applied',
                columns='status',
                aggfunc='size',
                fill_value=0,
            ).T
            st.plotly_chart(
                px.imshow(
                    pivot,
                    aspect="auto",
                    title='Monthly Status Heatmap',
                    color_continuous_scale='YlGnBu',
                ),
                use_container_width=True,
            )

    def show_reminders(self):
        with st.expander("🔔 Follow-up Reminders & Recents"):
            today = pd.to_datetime("today").normalize()
            self.filtered_df['follow_up_date'] = pd.to_datetime(
                self.filtered_df['follow_up_date'], errors='coerce'
            )
            upcoming = self.filtered_df[self.filtered_df['follow_up_date'] >= today]
            recent = self.filtered_df.sort_values(
                by='date_applied', ascending=False
            ).head(5)

            col1, col2 = st.columns(2)
            col1.markdown("**📬 Upcoming Follow-ups**")
            (
                col1.dataframe(
                    upcoming[
                        [
                            'company_name',
                            'job_title',
                            'follow_up_date',
                            'notes',
                        ]
                    ]
                )
                if not upcoming.empty
                else col1.write("No upcoming follow-ups.")
            )

            col2.markdown("**🕑 Recent Applications**")
            col2.dataframe(
                recent[['company_name', 'job_title', 'date_applied', 'status']]
            )


def analytics_ui(conn):
    st.subheader("📊 Analytics Dashbaord")

    engine = JobAnalyticsEngine(conn)

    if engine.df.empty:
        st.warning("No applications yet! Add some to see insights.")
        return

    st.sidebar.header("🧮 Filter Options")
    status_filter = st.sidebar.multiselect(
        "Select Status",
        engine.df['status'].unique(),
        default=list(engine.df['status'].unique()),
    )
    priority_filter = st.sidebar.multiselect(
        "Select Priority",
        engine.df['priority'].unique(),
        default=list(engine.df['priority'].unique()),
    )
    date_range = st.sidebar.date_input(
        "Select Date Range",
        [engine.df['date_applied'].min(), engine.df['date_applied'].max()],
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
