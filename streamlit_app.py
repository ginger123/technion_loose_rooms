#!/usr/bin/python3

import pytz
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import streamlit as st


HEBREW_DICT = {
    "מספר מקצוע": "course_num",
    "הרצאה / תרגיל": "group_num",
    "בניין": "building",
    "חדר": "room_num",
    "שעת התחלה": "start_time",
    "שעת סיום": "end_time",
}


@st.cache_data(ttl=3600)
def get_dataframe():
    return pd.read_html(
        "https://ugportal.technion.ac.il/%d7%94%d7%95%d7%a8%d7%90%d7%94-%d7%95%d7%91%d7%97%d7%99%d7%a0%d7%95%d7%aa/wintersemester-classes2025/",
        attrs={"id": "tablepress-99"},
    ).pop()


def parse_df(df):
    df = df.rename(columns=HEBREW_DICT, errors="raise")
    df["start_time"] = pd.to_datetime(df["start_time"], format="%m/%d/%Y %I:%M:%S %p")
    df["end_time"] = pd.to_datetime(df["end_time"], format="%m/%d/%Y %I:%M:%S %p")
    return df


def get_all_occupied_rooms(df, start_time, end_time):
    mask = ((df["start_time"] < start_time) & (df["end_time"] > start_time)) | (
        (df["start_time"] < end_time) & (df["end_time"] > end_time)
    )
    return df.loc[mask]


def run():

    st.title("Technion Room finder")
    st.header("Technion Room finder")
    st.write("Please select a time and date")
    # Input data
    jerusalem_tz = pytz.timezone('Asia/Jerusalem')
    now_in_israel = pytz.utc.localize(datetime.utcnow()).astimezone(jerusalem_tz)
    if 'start_time' not in st.session_state:
        st.session_state.start_time = now_in_israel
        st.session_state.end_time = now_in_israel + timedelta(minutes=30)
    select_date = st.date_input("Enter day", value=now_in_israel)
    st.session_state.start_time = st.time_input("Enter start time", st.session_state.start_time)
    st.session_state.end_time = st.time_input("Enter end time", st.session_state.end_time)

    if st.session_state.end_time < st.session_state.start_time:
        st.error("end time < start time!")
        return
    text_search = st.text_input("filter buildings")

    # combine to datetime
    start_datetime = datetime.combine(select_date, st.session_state.start_time)
    end_datetime = datetime.combine(select_date, st.session_state.end_time)

    # get data and analyze
    df = get_dataframe()
    df = parse_df(df)
    unique_rooms = set(df.building.unique())

    occupied_rooms = set(
        get_all_occupied_rooms(df, start_datetime, end_datetime).building.unique()
    )
    un_occupied = unique_rooms - occupied_rooms

    filter_for_user = [{"building": i} for i in un_occupied if text_search in i]
    un_occupied_df = pd.DataFrame(filter_for_user)
    selected_building = st.dataframe(
        un_occupied_df,
        height=25 * 36,
        on_select="rerun",
        selection_mode="single-row",
        use_container_width=True
        
    )
    # st.write(dir(selected_building))
    # st.write(str(selected_building.selection))
    for row in selected_building.selection['rows']:
        building = un_occupied_df.iloc[row]['building']
        st.write(building)
        mask = (df['start_time'].dt.date == select_date) & (df['building'] == building)
        st.dataframe(df.loc[mask], use_container_width=True)


if __name__ == "__main__":
    run()
