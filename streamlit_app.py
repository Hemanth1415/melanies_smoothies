# Import Python packages
import streamlit as st
import requests

from snowflake.snowpark.functions import col, when_matched


# --------------------------------------------------
# Get the Snowflake session
# --------------------------------------------------

cnx = st.connection("snowflake")
session = cnx.session()


# --------------------------------------------------
# Get fruit options from Snowflake
# --------------------------------------------------

fruit_options = (
    session.table("smoothies.public.fruit_options")
    .select(
        col("FRUIT_NAME"),
        col("SEARCH_ON")
    )
    .collect()
)


# --------------------------------------------------
# Create a dictionary:
# FRUIT_NAME -> SEARCH_ON
# --------------------------------------------------

fruit_search_map = {
    row["FRUIT_NAME"]: row["SEARCH_ON"]
    for row in fruit_options
}


# --------------------------------------------------
# Create list of fruit names
# --------------------------------------------------

fruit_list = list(fruit_search_map.keys())


# --------------------------------------------------
# Title
# --------------------------------------------------

st.title(
    f":cup_with_straw: Example Streamlit App :cup_with_straw: "
    f"{st.__version__}"
)

st.write(
    """
    Choose the fruits you want in your custom Smoothie!
    """
)


# --------------------------------------------------
# Smoothie name
# --------------------------------------------------

name_on_order = st.text_input(
    "Name on the smoothie:"
)

st.write(
    "The name on the smoothie will be:",
    name_on_order
)


# --------------------------------------------------
# Select ingredients
# --------------------------------------------------

ingredients_list = st.multiselect(
    "Choose Up to 5 ingredients:",
    fruit_list,
    max_selections=5
)


# --------------------------------------------------
# Display nutrition information
# --------------------------------------------------

if ingredients_list:

    ingredients_string = ""

    for fruit_chosen in ingredients_list:

        # Add fruit to ingredients string
        ingredients_string += fruit_chosen + " "


        # --------------------------------------------------
        # Get SEARCH_ON value
        # --------------------------------------------------

        search_on = fruit_search_map[fruit_chosen]
        search_ons=pd_df.loc[pd_df['FRUIT_NAME']==fruit_chosen,'SEARCH_ON'].iloc[0]


        # # Display SEARCH_ON value
        # st.write(
        #     "The search value for ",
        #     fruit_chosen,
        #     " is ",
        #     search_on,
        #     "."
        # )


        # --------------------------------------------------
        # Display fruit name
        # --------------------------------------------------

        st.subheader(
            fruit_chosen + " Nutrition Information"
        )


        # --------------------------------------------------
        # Build API URL using SEARCH_ON
        # --------------------------------------------------

        api_url = (
            "https://my.smoothiefroot.com/api/fruit/{search_ons}"
            # + search_on
        )


        # --------------------------------------------------
        # Call API
        # --------------------------------------------------

        smoothiefroot_response = requests.get(
            api_url
        )


        # --------------------------------------------------
        # Display API response
        # --------------------------------------------------

        if smoothiefroot_response.status_code == 200:

            st.dataframe(
                smoothiefroot_response.json(),
                use_container_width=True
            )

        else:

            st.error(
                f"Unable to get nutrition information "
                f"for {fruit_chosen}."
            )


    # --------------------------------------------------
    # Display selected ingredients
    # --------------------------------------------------

    st.write(
        "Selected ingredients:",
        ingredients_string
    )


    # --------------------------------------------------
    # Insert statement
    # --------------------------------------------------

    my_insert_stmt = """
        INSERT INTO smoothies.public.orders
        (ingredients, name_on_order)
        VALUES (?, ?)
    """


    # --------------------------------------------------
    # Submit Order button
    # --------------------------------------------------

    time_to_insert = st.button(
        "Submit Order"
    )


    if time_to_insert:

        session.sql(
            my_insert_stmt,
            params=[
                ingredients_string,
                name_on_order
            ]
        ).collect()

        st.success(
            f"Your Smoothie is ordered! {name_on_order}",
            icon="✅"
        )


# --------------------------------------------------
# Display unfilled orders
# --------------------------------------------------

st.subheader(
    "Orders to be Filled"
)


orders_df = (
    session.table("smoothies.public.orders")
    .filter(
        col("ORDER_FILLED") == False
    )
    .to_pandas()
)


# --------------------------------------------------
# Display editor if there are orders
# --------------------------------------------------

if not orders_df.empty:

    editable_df = st.data_editor(
        orders_df,
        use_container_width=True,
        hide_index=True
    )


    # --------------------------------------------------
    # Submit changes button
    # --------------------------------------------------

    submitted = st.button(
        "Submit"
    )


    if submitted:

        # --------------------------------------------------
        # Convert edited Pandas DataFrame
        # back to Snowpark DataFrame
        # --------------------------------------------------

        edited_dataset = session.create_dataframe(
            editable_df
        )


        # --------------------------------------------------
        # Original ORDERS table
        # --------------------------------------------------

        og_dataset = session.table(
            "smoothies.public.orders"
        )


        # --------------------------------------------------
        # Merge changes
        # --------------------------------------------------

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

    st.info(
        "There are no unfilled orders."
    )
