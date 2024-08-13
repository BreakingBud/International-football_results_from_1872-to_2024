import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile
import os

# Define the file path and extraction directory
zip_file_path = 'football_data_matches_scorers_shootouts.zip'
extraction_dir = 'data/football_data/'

# Extract the zip file if it hasn't been extracted yet
if not os.path.exists(extraction_dir):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extraction_dir)

# Load the datasets
@st.cache_data
def load_data():
    goalscorers_df = pd.read_csv(extraction_dir + 'goalscorers.csv')
    results_df = pd.read_csv(extraction_dir + 'results.csv')
    
    # Ensure date columns are in datetime format
    goalscorers_df['date'] = pd.to_datetime(goalscorers_df['date'], errors='coerce')
    results_df['date'] = pd.to_datetime(results_df['date'], errors='coerce')
    
    # Merge goalscorers_df with results_df to get tournament information
    goalscorers_df = pd.merge(goalscorers_df, results_df[['date', 'home_team', 'away_team', 'tournament']], 
                              on=['date', 'home_team', 'away_team'], how='left')
    return goalscorers_df, results_df

goalscorers_df, results_df = load_data()

# Function to filter data for player-to-player analysis
def prepare_player_to_player_data(player1, player2, tournament, start_date, end_date):
    filtered_df = goalscorers_df[
        (goalscorers_df['scorer'].isin([player1, player2])) &
        (goalscorers_df['date'].between(start_date, end_date)) &
        (goalscorers_df['tournament'].str.contains(tournament, case=False, na=False))
    ]
    return filtered_df

# Set up the sidebar menu
st.sidebar.title("Navigation")
menu = st.sidebar.radio(
    "Go to",
    ("Introduction", "Head-to-Head Analysis", "Player-to-Player Analysis")
)

if menu == "Introduction":
    st.title("Football Analysis App")
    st.markdown("""
    ### Welcome to the Football Analysis App
    
    This application allows you to explore historical football match data, particularly focusing on head-to-head matchups between different teams and player-to-player analysis.
    
    Use the sidebar to navigate to different sections of the app.
    """)
    
elif menu == "Head-to-Head Analysis":
    # Define columns for layout
    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        # Team selection
        team1 = st.selectbox('Select Team 1', results_df['home_team'].unique())
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        team2 = st.selectbox('Select Team 2', results_df['home_team'].unique())
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        
        # Tournament selection
        tournament = st.selectbox('Select Tournament', ['All'] + sorted(results_df['tournament'].unique().tolist()))
        if tournament == 'All':
            tournament = ''  # Empty string will be used to match all tournaments
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

        # Date range selection
        min_date = results_df['date'].min()
        max_date = results_df['date'].max()
        date_range = st.slider(
            'Select Date Range',
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="YYYY-MM-DD"
        )

        start_date, end_date = date_range

    with col2:
        # Perform analysis
        head_to_head_df = prepare_head_to_head_data(team1, team2, tournament, start_date, end_date)

        total_matches = len(head_to_head_df)
        st.markdown(f"**{team1}** and **{team2}** played **{total_matches}** matches head to head.")

        # Show filtering information only if specific tournament is selected
        if tournament:
            tournament_display = tournament if tournament else "All tournaments"
            st.markdown(f"Filtering by tournament: **{tournament_display}**")

        # Label outcomes correctly
        head_to_head_df['outcome_label'] = head_to_head_df['outcome'].apply(
            lambda x: f'{team1} Win' if x == team1 else f'{team2} Win' if x == team2 else 'Draw'
        )

        # Correctly count unique outcomes
        outcome_counts = head_to_head_df['outcome_label'].value_counts(dropna=False)

        # Pie chart for outcomes
        fig = px.pie(outcome_counts, names=outcome_counts.index, values=outcome_counts.values, title="Win Rate")
        st.plotly_chart(fig, use_container_width=True)

        # Display shootout data
        shootout_matches = head_to_head_df[head_to_head_df['shootout'] == True]
        if not shootout_matches.empty:
            st.markdown("### Shootout Matches:")
            st.dataframe(shootout_matches[['date', 'home_team', 'away_team', 'winner']], use_container_width=True)
    pass

elif menu == "Player-to-Player Analysis":
    st.title("Player-to-Player Analysis")
    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        # Player selection
        player1 = st.selectbox('Select Player 1', goalscorers_df['scorer'].unique())
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        player2 = st.selectbox('Select Player 2', goalscorers_df['scorer'].unique())
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        
        # Tournament selection
        tournament = st.selectbox('Select Tournament', ['All'] + sorted(goalscorers_df['tournament'].unique().tolist()))
        if tournament == 'All':
            tournament = ''  # Empty string will be used to match all tournaments
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

        # Date range selection
        min_date = goalscorers_df['date'].min()
        max_date = goalscorers_df['date'].max()
        date_range = st.slider(
            'Select Date Range',
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="YYYY-MM-DD"
        )

        start_date, end_date = date_range

    with col2:
        # Perform analysis
        player_data_df = prepare_player_to_player_data(player1, player2, tournament, start_date, end_date)

        # Goal distribution pie chart
        player_goal_counts = player_data_df['scorer'].value_counts()
        fig = px.pie(player_goal_counts, names=player_goal_counts.index, values=player_goal_counts.values, title="Goals Distribution")
        st.plotly_chart(fig, use_container_width=True)

        # Penalty goals count
        penalty_goals = player_data_df[player_data_df['penalty'] == True]['scorer'].value_counts()
        st.markdown("### Penalty Goals")
        st.write(penalty_goals)

        # Goal minute distribution
        st.markdown("### Goal Minute Distribution")
        goal_minutes_df = player_data_df[['scorer', 'minute']]
        fig = px.histogram(goal_minutes_df, x='minute', color='scorer', nbins=10, title="Goal Scoring Minutes")
        st.plotly_chart(fig, use_container_width=True)
