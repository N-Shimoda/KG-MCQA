import streamlit as st


class MainPage:
    def __init__(self):
        self.title = "Main Page"
        self.description = "This is the main page of the Streamlit app."

        # config
        st.set_page_config(layout="wide")
        st.markdown(
            """
            <style>
                .block-container {
                    padding-bottom: 1rem;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

    def display(self):
        st.title(self.title)
        st.write(self.description)


if __name__ == "__main__":

    main = MainPage()
    main.display()
