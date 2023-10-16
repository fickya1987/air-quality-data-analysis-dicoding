import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as PC

url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTXFKefF7-wy_GWu-tWyI9BFW_HYNB16mGO5yCkQ57I_JraswJO6LHmXEpMjE4myWB_nH2bPP--sQwm/pub?gid=0&single=true&output=csv'
data = pd.read_csv(url)
data['datetime'] = pd.to_datetime(data['datetime'])

pollutant_parameters = list(data.columns[:6])
weather_parameters = list(data.columns[6:10]) + [data.columns[11]]

# Define the custom category order
custom_category_order = [
    "Good",
    "Moderate",
    "Unhealthy for Sensitive Groups",
    "Unhealthy",
    "Very Unhealthy",
    "Hazardous"
]

st.title('Air Quality Dashboard 2013 - 2017 in 12 Beijing Stations')
with st.sidebar:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(' ')
    with col2:
        st.image("https://cdn1.iconfinder.com/data/icons/air-pollution-21/62/Air-quality-mask-pollution-protection-256.png"
                 , width=100)
    with col3:
        st.write(' ')
    st.header('Filters')


# Station filter with multiselect
selected_stations = st.sidebar.multiselect('Select Stations', ['Overall Station'] + list(data['station'].unique()))

selected_category = st.sidebar.selectbox('Select Category',
                                         ['Overall Category'] + list(data['Category'].unique()), index=0)
start_date = st.sidebar.date_input('Start Date', min(data['datetime']).date(),
                                   min_value=pd.to_datetime('2013-03-01').date(),
                                   max_value=pd.to_datetime('2017-02-28').date())
end_date = st.sidebar.date_input('End Date', max(data['datetime']).date(),
                                 min_value=pd.to_datetime('2013-03-01').date(),
                                 max_value=pd.to_datetime('2017-02-28').date())
start_hour = st.sidebar.slider('Start Hour', 0, 23, 0)
end_hour = st.sidebar.slider('End Hour', 0, 23, 23)

# Filter data based on selected stations
if 'Overall Station' in selected_stations:
    selected_stations.remove('Overall Station')

start_datetime = pd.to_datetime(start_date).date
end_datetime = pd.to_datetime(end_date).date
data['date'] = data['datetime'].dt.date
data['Hour'] = data['datetime'].dt.hour

# Filter data based on selected stations
if 'Overall Station' in selected_stations:
    selected_stations.remove('Overall Station')

if selected_category == 'Overall Category' and not selected_stations:
    # If no specific stations are selected, use all stations
    filtered_data = data[(data['date'] >= start_datetime()) & (data['date'] <= end_datetime()) &
                         (data['Hour'] >= start_hour) & (data['Hour'] <= end_hour)]
elif not selected_stations:
    filtered_data = data[(data['Category'] == selected_category) &
                         (data['date'] >= start_datetime()) & (data['date'] <= end_datetime()) &
                         (data['Hour'] >= start_hour) & (data['Hour'] <= end_hour)]
elif selected_category == 'Overall Category':
    filtered_data = data[(data['station'].isin(selected_stations)) &
                         (data['date'] >= start_datetime()) & (data['date'] <= end_datetime()) &
                         (data['Hour'] >= start_hour) & (data['Hour'] <= end_hour)]
else:
    filtered_data = data[(data['station'].isin(selected_stations)) & (data['Category'] == selected_category) &
                         (data['date'] >= start_datetime()) & (data['date'] <= end_datetime()) &
                         (data['Hour'] >= start_hour) & (data['Hour'] <= end_hour)]


selected_station_str = ', '.join(selected_stations) if selected_stations else 'All Stations'
st.write(f"**Key Metrics for {selected_station_str} - {selected_category}**")
category_counts = filtered_data.groupby('Category')['datetime'].nunique()
cols = st.columns(3)
for index, (category, count) in enumerate(category_counts.items()):
    formatted_count = "{:,}".format(count)  # Format count with commas for thousands
    col = cols[index % 3]  # Cycle through the columns (3 columns)
    col.metric(category, f"{formatted_count} Days")


# Calculate counts for each category and set the custom order
category_counts = data['Category'].value_counts().reset_index()
category_counts.columns = ['Category', 'Count']
category_counts['Category'] = pd.Categorical(category_counts['Category'], categories=custom_category_order, ordered=True)
category_counts = category_counts.sort_values('Category')

# Create a pie chart
fig = px.pie(category_counts, values='Count', names='Category', title='Air Quality Categories Percentage')

# Display the chart in Streamlit
st.plotly_chart(fig)


col1, col2 = st.columns(2)
with col1:
    selected_parameter = st.selectbox('Select Air Pollutant Parameter', pollutant_parameters)
with col2:
    frequency_options = ['Hourly', 'Daily', 'Weekly', 'Monthly', 'Yearly']
    selected_frequency = st.selectbox('Select Time Frequency', frequency_options)

# Plot the chart for the selected stations
filtered_data_resampled = filtered_data.groupby(['station',
                                                 pd.Grouper(key='datetime',
                                                            freq=selected_frequency[0])])[selected_parameter].mean().reset_index()
fig = px.line(filtered_data_resampled, x='datetime', y=selected_parameter, color='station',
              title=f'{selected_parameter} {selected_frequency} Levels by Station Over Time')
st.plotly_chart(fig)


# Display Scatter Plot
col1, col2 = st.columns(2)
with col1:
    selected_parameter1 = st.selectbox('Select Parameter 1', pollutant_parameters + weather_parameters)
with col2:
    selected_parameter2 = st.selectbox('Select Parameter 2', pollutant_parameters + weather_parameters)

fig_scatter = px.scatter(filtered_data, x=selected_parameter1, y=selected_parameter2,
                         color='station', title=f'{selected_parameter1} vs. {selected_parameter2} Correlation')
st.plotly_chart(fig_scatter)


# Group and pivot the data to get the counts for each category and station
pivot_data = filtered_data.pivot_table(index='station', columns='Category', values='PM2.5', aggfunc='count', fill_value=0)

# Create a stacked bar chart
fig = px.bar(pivot_data, x=pivot_data.index, y=custom_category_order, title='Air Quality by Station',
             labels={'station': 'Station', 'value': 'Count', 'variable': 'Category'},
             color_discrete_sequence=px.colors.qualitative.Set3)
fig.update_layout(barmode='stack')

# Display the chart in Streamlit
st.plotly_chart(fig)


# Map categories to a numerical order based on the custom order
category_order_mapping = {category: i for i, category in enumerate(custom_category_order)}

# Assign a numerical order to each row in the dataset
data['Category_Order'] = filtered_data['Category'].map(category_order_mapping)

# Group and aggregate data
grouped_data = data.groupby(['wd', 'Category']).size().reset_index(name='count')

# Sort the data based on the custom category order and category order mapping
grouped_data['Category_Order'] = grouped_data['Category'].map(category_order_mapping)
grouped_data = grouped_data.sort_values(by=['Category_Order', 'wd'])

# Create a colormap with varying shades of a single color (e.g., blue)
color_scale = pc.sequential.Blues

# Create polar bar chart
fig = go.Figure()

categories = custom_category_order

for i, category in enumerate(categories):
    category_data = grouped_data[grouped_data['Category'] == category]
    color = color_scale[i]  # Get a shade of blue from the colormap
    fig.add_trace(go.Barpolar(
        r=category_data['count'],
        theta=category_data['wd'],
        name=category,
        text=category_data['count'],
        hoverinfo='text',
        marker=dict(color=color)
    ))

fig.update_layout(
    polar=dict(
        radialaxis=dict(visible=True, range=[0, max(grouped_data['count'])])
    ),
    title="Air Quality by Wind Direction",
)

# Display the chart in Streamlit
st.plotly_chart(fig)
