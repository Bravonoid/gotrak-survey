import streamlit as st
import pandas as pd
import json
import seaborn as sns
import matplotlib.pyplot as plt

import database

st.title("Ergonomics Survey Management")

# Navbar
nav = st.sidebar.radio("Navigation", ["Sample", "Analyze", "Visualize"])

if nav == "Sample":
    # Display current target sample from database
    st.header("Current Target Sample")
    st.write("The current target sample is displayed below")
    st.write("You can update the target sample by uploading an excel file")

    # Get all documents from a collection
    result = database.get_all_documents(database.sample)

    # Convert to dataframe
    df = pd.DataFrame(result)

    # Drop _id column
    df.drop("_id", axis=1, inplace=True)

    # Display the data
    st.write(df)

    # Upload/Update sample
    st.header("Update Target Sample Here")
    st.write("Upload an excel file containing the target sample here")

    uploaded_file = st.file_uploader("Choose a file", type=["xlsx"])

    if uploaded_file is not None:
        # Read pandas multiple sheets
        df = pd.read_excel(uploaded_file, sheet_name=None)

        # Display the data
        # st.write(df)

        # # Get sheet names
        divisions = list(df.keys())

        # Exclude 'Achievement' sheet
        divisions.remove("Achievement")

        # Save division as json
        with open("divisions.json", "w") as f:
            json.dump(divisions, f)

        # Get business unit, department, PEG, and Jumlah sampel
        fail_to_analyze = []
        data = []
        for division in divisions:
            # Rename columns that has 'Jumlah Sampel' in it to 'Jumlah Sampel'
            columns = df[division].columns
            for column in columns:
                if "Jumlah Sampel" in column:
                    df[division].rename(columns={column: "Jumlah Sampel"}, inplace=True)

            # Remove column except for 'Business Unit', 'Department', 'PEG', and 'Jumlah Sampel'
            df[division] = df[division][
                [
                    "Business Unit",
                    "Department",
                    "Potential Exposured Group (PEG)",
                    "Jumlah Sampel",
                ]
            ]

            # Round 'Jumlah Sampel' to 0 decimal places
            df[division]["Jumlah Sampel"] = df[division]["Jumlah Sampel"].round(0)

            # Replace empty data on department with '-'
            df[division]["Department"].fillna("-", inplace=True)

            # Remove empty rows
            df[division].dropna(subset=["Business Unit"], inplace=True)

            st.write(division)
            st.write(df[division])

            # Append data
            data.append(df[division])

        # Send to database
        if data:
            with st.spinner("Inserting data to database..."):
                database.insert_update_sample(data)

        if fail_to_analyze:
            st.header("Failed to Analyze")
            st.write(
                "Division that are failed to analyze may not have **'Business Unit', 'Department', 'Potential Exposured Group (PEG)', and 'Jumlah Sampel'** columns."
            )
            st.write("Please check the columns name correctly and re-upload the file.")
            st.write(fail_to_analyze)

if nav == "Analyze":
    st.header("Analyze the Data")
    st.write("Make sure the file name have the **division name**")

    # Get the total sample data from database
    samples = database.get_all_documents(database.sample)

    # Convert to dataframe
    samples = pd.DataFrame(samples)

    # Drop _id column
    samples.drop("_id", axis=1, inplace=True)

    # Get division name from database
    divisions = samples["Business Unit"].unique()

    # Display divisions available
    st.write("Divisions available:")
    st.write(divisions)

    st.write(
        "Check if the columns name are correct, minimum columns are **'Department', 'Potential Exposured Group (PEG)', and 'Survey Answers'**"
    )

    uploaded_file = st.file_uploader("Choose a file", type=["xlsx"])

    if uploaded_file is not None:
        # Get division name from file name
        file_name = uploaded_file.name.split(".")[0]

        division = ""
        for d in divisions:
            if d.lower() in file_name.lower():
                division = d
                break

        if not division:
            st.write("Division not found in the file name")
            st.write("Please make sure the file name have the division name")
            st.stop()

        # Display the division name
        st.subheader(f"Division: *{division}*")

        df = pd.read_excel(uploaded_file, sheet_name=None)

        # Take only the first sheet
        responses = list(df.keys())[0]

        df = df[responses]

        # Remove specified columns
        df = df.drop(
            [
                "ID",
                "Start time",
                "Completion time",
                "Email",
                "Name",
                "Last modified time",
                "Nomor ID",
            ],
            axis=1,
        )

        # Find column that have Pernahkah Anda mengalami rasa sakit/nyeri atau ketidaknyaman yang Anda anggap berhubungan dengan pekerjaan dalam satu tahun terakhir? in it
        determining_factor = [
            column
            for column in df.columns
            if "Pernahkah Anda mengalami rasa sakit/nyeri atau ketidaknyaman yang Anda anggap berhubungan dengan pekerjaan dalam satu tahun terakhir?"
            in column
        ]

        # Check for column that have "Potential Exposured Group (PEG)" in it
        peg = [
            column
            for column in df.columns
            if "Potential Exposured Group (PEG)" in column
        ]

        # Rename specified columns
        df.rename(
            columns={
                "Departemen": "Department",
                peg[0]: "Potential Exposured Group (PEG)",
                determining_factor[0]: "Determining Factor",
            },
            inplace=True,
        )

        # Display the data
        st.write(df)

        # Get the department
        departments = df["Department"].unique()

        # Get the PEG
        pegs = df["Potential Exposured Group (PEG)"].unique()

        data = []
        # Loop through the department and PEG
        for department in departments:
            for peg in df[df["Department"] == department][
                "Potential Exposured Group (PEG)"
            ].unique():
                st.subheader(f"{department} - {peg}")

                # Get total sample
                total_sample = samples[
                    (samples["Department"] == department) & (samples["PEG"] == peg)
                ]["Jumlah Sampel"].values

                if total_sample.size > 0:
                    total_sample = int(total_sample[0])
                else:
                    total_sample = 0

                # Get determining factor
                determining_factor = df[
                    (df["Department"] == department)
                    & (df["Potential Exposured Group (PEG)"] == peg)
                ]["Determining Factor"].value_counts()

                st.write(f"Total sample: {total_sample}")

                st.write(determining_factor)

                # Get yes and no
                yes = determining_factor["Ya"] if "Ya" in determining_factor else 0
                no = determining_factor["Tidak"] if "Tidak" in determining_factor else 0

                # Get percentage
                percentage = (yes / total_sample) * 100 if total_sample else 0
                percentage = round(percentage, 2)

                # # Display percentage
                st.write(f"Percentage: **{percentage}%**")

                survey_responses = df[
                    (df["Department"] == department)
                    & (df["Potential Exposured Group (PEG)"] == peg)
                ]

                # Remove 'Determining Factor' column
                survey_responses = survey_responses.drop(
                    [
                        "Determining Factor",
                        "Department",
                        "Potential Exposured Group (PEG)",
                    ],
                    axis=1,
                )

                # Convert to dictionary
                survey_responses = survey_responses.to_dict(orient="records")

                # Convert NaN to "-"
                for response in survey_responses:
                    for key, value in response.items():
                        if pd.isna(value):
                            response[key] = "-"

                # Append data
                data.append(
                    {
                        "Business Unit": division,
                        "Department": department,
                        "PEG": peg,
                        "Total Sample": total_sample,
                        "Yes": yes,
                        "No": no,
                        "Percentage": percentage,
                        "Survey Responses": survey_responses,
                    }
                )

        # Save to database
        if data:
            # Cast numpy int to int
            for d in data:
                d["Total Sample"] = int(d["Total Sample"])
                d["Yes"] = int(d["Yes"])
                d["No"] = int(d["No"])

            with open("data.json", "w") as f:
                json.dump(data, f)

            with st.spinner("Inserting data to database..."):
                database.insert_update_achievment(data)

if nav == "Visualize":
    st.header("Visualize the Data")
    st.write("Visualize the data here")

    # Get all documents from a collection
    result = database.get_all_documents(database.achievment)

    # Convert to dataframe
    df = pd.DataFrame(result)

    # Drop _id column
    df.drop("_id", axis=1, inplace=True)

    # Display the data
    st.write(df)

    # Create barchart for each group of division, department, and PEG. The barchart will show the percentage
    for division in df["Business Unit"].unique():
        st.header(division)

        st.subheader("Visualization")

        # Get data
        data = df[df["Business Unit"] == division]

        # Create barchart
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=data, x="Department", y="Percentage", hue="PEG", ax=ax)
        plt.title("Percentage of Yes")
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Put legend outside the plot
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

        # Put a line on 30%
        plt.axhline(y=30, color="r", linestyle="--")

        # Display barchart
        st.pyplot(fig)

        # List all of the department and PEG that are more than 30%
        st.write("List of department and PEG that are more than 30%")

        filtered = data[data["Percentage"] > 30]
        # Remove 'Business Unit'
        filtered = filtered.drop(["Business Unit", "Survey Responses"], axis=1)

        # Rearrange the columns
        filtered = filtered[
            ["Department", "PEG", "Percentage", "Total Sample", "Yes", "No"]
        ]

        st.write(filtered)

        # Detailed survey responses
        st.subheader("Detailed survey responses")

        col1, col2 = st.columns(2)

        department = col1.selectbox("Department", data["Department"].unique())
        peg = col2.selectbox("PEG", data["PEG"].unique())

        # Get survey responses
        survey_responses = data[
            (data["Department"] == department) & (data["PEG"] == peg)
        ]["Survey Responses"].values

        if survey_responses.size > 0:
            survey_responses = survey_responses[0]

            # Convert to dataframe
            survey_responses = pd.DataFrame(survey_responses)

            # Display the data
            st.write(survey_responses)
        else:
            st.write("No survey responses available")

        st.write("---")
