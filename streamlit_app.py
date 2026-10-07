# Import Python packages
import streamlit as st
import pandas as pd
import requests 
# from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col, when_matched
# Get data from Smoothie Froot API
api_url = "https://my.smoothiefroot.com/api/fruit/watermelon"
smoothiefroot_response = requests.get(api_url)


# Display the JSON response
st.text(smoothiefroot_response.json())

# st.title('My parents New Healthy Diner')
# Get the active Snowflake session
cnx=st.connection("snowflake")
# session = get_active_session()
session = cnx.session()


# Title
st.title(f":cup_with_straw: Example Streamlit App :cup_with_straw: {st.__version__}")

st.write(
    """
    Choose the fruits you want in your custom Smoothie!
    """
)


# Get fruit options
fruit_options = (
    session.table("smoothies.public.fruit_options")
    .select(col("FRUIT_NAME"))
    .collect()
)

fruit_list = [row["FRUIT_NAME"] for row in fruit_options]


# Smoothie name
name_on_order = st.text_input("Name on the smoothie:")

st.write(
    "The name on the smoothie will be:",
    name_on_order
)


# Select ingredients
ingredients_list = st.multiselect(
    "Choose Up to 5 ingredients:",
    fruit_list,max_selections=5
)


if ingredients_list:

    ingredients_string = ""

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + " "

    st.write(ingredients_string)


    # Insert statement
    my_insert_stmt = """
        INSERT INTO smoothies.public.orders
        (ingredients, name_on_order)
        VALUES (?, ?)
    """


    # Submit Order button
    time_to_insert = st.button("Submit Order")


    if time_to_insert:

        session.sql(
            my_insert_stmt,
            params=[ingredients_string, name_on_order]
        ).collect()

        st.success(
            f"Your Smoothie is ordered! {name_on_order}",
            icon="✅"
        )


# --------------------------------------------------
# Display unfilled orders
# --------------------------------------------------

st.subheader("Orders to be Filled")


orders_df = (
    session.table("smoothies.public.orders")
    .filter(col("ORDER_FILLED") == False)
    .to_pandas()
)


# Only display the editor if there are orders
if not orders_df.empty:

    editable_df = st.data_editor(
        orders_df,
        use_container_width=True,
        hide_index=True
    )


    # Submit changes button
    submitted = st.button("Submit")


    if submitted:

        # Convert edited Pandas DataFrame back to Snowpark DataFrame
        edited_dataset = session.create_dataframe(editable_df)


        # Original ORDERS table
        og_dataset = session.table(
            "smoothies.public.orders"
        )


        # Merge the changes
        og_dataset.merge(
            edited_dataset,
            (
                og_dataset["ORDER_UID"]
                == edited_dataset["ORDER_UID"]
            ),
            [
                when_matched().update(
                    {
                        "ORDER_FILLED":
                        edited_dataset["ORDER_FILLED"]
                    }
                )
            ]
        )


        st.success(
            "Order status updated successfully! ✅"
        )

else:

    st.info("There are no unfilled orders.")
