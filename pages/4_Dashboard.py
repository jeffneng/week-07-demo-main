import json

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide", page_title="Course Dashboard")


@st.cache_data
def load_courses() -> pd.DataFrame:
    with open('./data/courses-full.json', 'r', encoding='utf-8') as file:
        courses = json.load(file)
    df = pd.DataFrame(list(courses.values()))
    df['duration_weeks'] = df['duration'].str.extract(r'(\d+)').astype(int)
    df['price_per_week'] = (df['price'] / df['duration_weeks']).round(2)
    df['value_score'] = (df['rating'] / df['price'] * 1000).round(2)  # rating points per $1,000
    df['skills'] = df['skills_covered'].apply(', '.join)
    return df


df = load_courses()

st.title("Course Dashboard")

# region <--------- Sidebar filters --------->
st.sidebar.header("Filters")
categories = st.sidebar.multiselect("Category", sorted(df['category'].unique()))
providers = st.sidebar.multiselect("Provider", sorted(df['provider'].unique()))
price_min, price_max = float(df['price'].min()), float(df['price'].max())
price_range = st.sidebar.slider("Price range ($)", price_min, price_max, (price_min, price_max))
min_rating = st.sidebar.slider("Minimum rating", 4.0, 5.0, 4.0, 0.1)
skill_search = st.sidebar.text_input("Search skill (e.g. Python)")

filtered = df[df['price'].between(*price_range) & (df['rating'] >= min_rating)]
if categories:
    filtered = filtered[filtered['category'].isin(categories)]
if providers:
    filtered = filtered[filtered['provider'].isin(providers)]
if skill_search:
    filtered = filtered[filtered['skills'].str.contains(skill_search, case=False)]
# endregion <--------- Sidebar filters --------->

if filtered.empty:
    st.warning("No courses match the current filters.")
    st.stop()

# region <--------- KPI cards --------->
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Courses", len(filtered))
k2.metric("Avg price", f"${filtered['price'].mean():,.0f}")
k3.metric("Avg rating", f"{filtered['rating'].mean():.2f}")
k4.metric("Categories", filtered['category'].nunique())
k5.metric("Providers", filtered['provider'].nunique())
best = filtered.sort_values('value_score', ascending=False).iloc[0]
st.info(f"**Best value:** {best['name']} ({best['provider']}) - rating {best['rating']} at ${best['price']:,.2f}")
# endregion <--------- KPI cards --------->

# region <--------- Charts --------->
c1, c2 = st.columns(2)

with c1:
    st.subheader("Price vs rating")
    scatter = alt.Chart(filtered).mark_circle(size=140).encode(
        x=alt.X('price:Q', title='Price ($)', scale=alt.Scale(zero=False)),
        y=alt.Y('rating:Q', title='Rating', scale=alt.Scale(zero=False)),
        color='category:N',
        tooltip=['name', 'provider', 'category', 'price', 'rating', 'duration'],
    ).interactive()
    st.altair_chart(scatter, use_container_width=True)

with c2:
    st.subheader("Average price by category")
    by_cat = filtered.groupby('category', as_index=False)['price'].mean().round(2)
    bars = alt.Chart(by_cat).mark_bar().encode(
        x=alt.X('price:Q', title='Avg price ($)'),
        y=alt.Y('category:N', sort='-x', title=None),
        color=alt.Color('category:N', legend=None),
        tooltip=['category', 'price'],
    )
    st.altair_chart(bars, use_container_width=True)

c3, c4 = st.columns(2)

with c3:
    st.subheader("Average rating by provider")
    by_prov = filtered.groupby('provider', as_index=False)['rating'].mean().round(2)
    bars = alt.Chart(by_prov).mark_bar().encode(
        x=alt.X('rating:Q', title='Avg rating', scale=alt.Scale(domain=[4, 5])),
        y=alt.Y('provider:N', sort='-x', title=None),
        tooltip=['provider', 'rating'],
    )
    st.altair_chart(bars, use_container_width=True)

with c4:
    st.subheader("Duration vs price")
    dur = alt.Chart(filtered).mark_circle(size=140).encode(
        x=alt.X('duration_weeks:Q', title='Duration (weeks)'),
        y=alt.Y('price:Q', title='Price ($)', scale=alt.Scale(zero=False)),
        color='category:N',
        tooltip=['name', 'duration', 'price', 'price_per_week'],
    ).interactive()
    st.altair_chart(dur, use_container_width=True)

c5, c6 = st.columns(2)

with c5:
    st.subheader("Most-covered skills")
    skills = filtered['skills_covered'].explode().value_counts().head(10).reset_index()
    skills.columns = ['skill', 'courses']
    bars = alt.Chart(skills).mark_bar().encode(
        x=alt.X('courses:Q', title='Courses', axis=alt.Axis(tickMinStep=1)),
        y=alt.Y('skill:N', sort='-x', title=None),
        tooltip=['skill', 'courses'],
    )
    st.altair_chart(bars, use_container_width=True)

with c6:
    st.subheader("Courses per category")
    counts = filtered['category'].value_counts().reset_index()
    counts.columns = ['category', 'courses']
    donut = alt.Chart(counts).mark_arc(innerRadius=60).encode(
        theta='courses:Q',
        color='category:N',
        tooltip=['category', 'courses'],
    )
    st.altair_chart(donut, use_container_width=True)
# endregion <--------- Charts --------->

# region <--------- Course table --------->
st.subheader("Courses")
st.dataframe(
    filtered[['name', 'category', 'provider', 'duration', 'rating', 'price', 'price_per_week', 'skills']]
    .sort_values('rating', ascending=False),
    use_container_width=True,
    hide_index=True,
)
# endregion <--------- Course table --------->

# region <--------- Compare two courses --------->
st.subheader("Compare two courses")
names = sorted(df['name'])
a_col, b_col = st.columns(2)
course_a = a_col.selectbox("Course A", names, index=0)
course_b = b_col.selectbox("Course B", names, index=min(1, len(names) - 1))

compare = df.set_index('name').loc[[course_a, course_b],
                                   ['category', 'provider', 'duration', 'rating', 'price', 'price_per_week', 'skills', 'description']].astype(str).T
st.table(compare)
# endregion <--------- Compare two courses --------->
