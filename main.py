import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

# Name of the application
st.set_page_config(
    page_title="Simple Financial Indicator Dashboard", page_icon="💰", layout="wide"
)

category_file = "categories.json"

# Manual Categorization of different categories
if "categories" not in st.session_state:
    st.session_state.categories = {"Uncategorized": []}

# Load the state of the file categories.json if it exists
# Also open the file on read mode
# With the Load we load it as JSON = Python Dictionary
if os.path.exists(category_file):
    with open(category_file, "r") as f:
        st.session_state.categories = json.load(f)


def save_categories():
    with open(category_file, "w") as f:
        json.dump(st.session_state.categories, f)


def categorize_transactions(df):
    # Add a new column category
    df["Category"] = "Uncategorized"

    # Check the list of all transactions
    for category, keywords in st.session_state.categories.items():

        if category == "Uncategorized" or not keywords:
            continue

        # Create a new list of keywords and then make them lower case
        lowered_keywords = [kw.lower().strip() for kw in keywords]

        # Iterate in each row of the dataframe
        for idx, row in df.iterrows():
            # Access the values of the row
            details = row["Details"].lower().strip()

            # Check if the values are in lowered keywords
            if details in lowered_keywords:
                df.at[idx, "Category"] = category

    return df


# This method reads the data from the file
def load_transactions(file):
    # use try and except block
    try:
        # Read the data from the file
        df = pd.read_csv(file)

        # display the dataframe to the streamlit
        st.write(df)

        # it removes leading and trailing whitespaces from all the column names in the DF
        df.columns = [col.strip() for col in df.columns]

        # Replace the comma with a space
        df["Amount"] = df["Amount"].str.replace(",", "").astype(float)

        # Change the date to datetime, date,  name of month and year
        df["Date"] = pd.to_datetime(df["Date"], format="%d %b %Y")

        return categorize_transactions(df)

    # Create the exception block
    except Exception as e:
        # Throw the error for processing the files
        st.error(f"Error processing the files: {str(e)}")

        return None


# With this function I want to add the details for each of my categories
def add_keyword_to_category(category, keyword):
    keyword = keyword.strip()
    if keyword and keyword not in st.session_state.categories[category]:
        st.session_state.categories[category].append(keyword)
        save_categories()
        return True
    return False


def main():

    # Title of the Dashboard
    st.title("Simple Financial Indicator Dashboard")

    # Upload a file as a type of csv
    uploaded_file = st.file_uploader(
        "Please upload your transaction CSV file", type=["csv"]
    )

    # Check if the file exists or not
    if uploaded_file is not None:

        # Use the load transaction method to load the data from the file
        df = load_transactions(uploaded_file)

        if df is not None:
            # Get a dataframe for debits
            debits_df = df[df["Debit/Credit"] == "Debit"].copy()

            # Get the dataframe of credits
            credits_df = df[df["Debit/Credit"] == "Credit"].copy()

            # Copy the session state of the debits
            st.session_state.debits_df = debits_df.copy()

            # Write some tabs to see the Debit or Credit dataframe
            tab1, tab2 = st.tabs(["Expenses (Debits)", "Payments (Credits)"])

            # First tab will work for debits
            with tab1:
                # New category
                new_category = st.text_input("New Category Name")

                # Adding the button to add a category
                add_button = st.button("Add Category")

                # If both exist and the category is not in the state
                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        st.rerun()

                # Make the debits dataframe an editable dataframe
                st.subheader("Your Expenses")

                # Configure the editable dataframe
                edited_df = st.data_editor(
                    # I want to put a list of columns I want to display
                    st.session_state.debits_df[
                        ["Date", "Details", "Amount", "Category"]
                    ],
                    # Configure each column
                    column_config={
                        "Date": st.column_config.DateColumn(
                            "Date", format="DD/MM/YYYY"
                        ),
                        "Amount": st.column_config.NumberColumn(
                            "Amount", format="%.2f"
                        ),
                        "Category": st.column_config.SelectboxColumn(
                            "Category", options=list(st.session_state.categories.keys())
                        ),
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="category_editor",
                )

                # add the saving button
                save_button = st.button("Apply Changes", type="primary")

                # Create the saving functionality
                if save_button:
                    # Read each index and row in the edited df
                    for idx, row in edited_df.iterrows():
                        # the new category will come from the row category
                        new_category = row["Category"]
                        # If the new category exists then continue
                        if (
                            new_category
                            == st.session_state.debits_df.at[idx, "Category"]
                        ):
                            continue

                        # Details will come from the row of details
                        details = row["Details"]

                        st.session_state.debits_df.at[idx, "Category"] = new_category
                        # When the user picks the category then it will be added to the df
                        add_keyword_to_category(new_category, details)

            # Create the charts
            st.subheader("Expense Summary Total")

            # Group by the category and amount
            category_totals = (
                st.session_state.debits_df.groupby("Category")["Amount"]
                .sum()
                .reset_index()
            )

            # Sort the category totals in a descending order
            category_totals = category_totals.sort_values("Amount", ascending=False)

            # Display that as an additional dataframe
            st.dataframe(
                category_totals,
                column_config={
                    "Amount": st.column_config.NumberColumn("Amount", format="%.2f")
                },
                use_container_width=True,
                hide_index=True,
            )

            # Display a chart on screen, using plotly express
            fig = px.pie(
                category_totals,
                values="Amount",
                names="Category",
                title="Expenses By Each Category",
            )
            # Show the chart and take the entire width of the screen
            st.plotly_chart(fig, use_container_width=True)

            # Second tab will work for credits
            with tab2:
                st.subheader("Income Summary")
                total_payments = credits_df["Amount"].sum()
                st.metric("Total Payments", f"{total_payments: ,.2f}")
                st.write(credits_df)


# run the main method
main()
