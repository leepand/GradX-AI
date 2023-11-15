import streamlit as st
from PIL import Image
from tools.st_functions import st_button


class About:
    class Model:
        pageTitle = "About"

    def view(self, model):
        # st.title(model.pageTitle)

        #st.write(
        #    "[![Star](https://img.shields.io/github/stars/katanaml/sparrow.svg?logo=github&style=social)](https://github.com/katanaml/sparrow)")

        col1, col2, col3 = st.columns(3)
        col2.image(Image.open('assets/machine.jpg'))

        st.markdown("<h1 style='text-align: center; color: black; font-weight: bold;'>OptX-AI</h1>",
                    unsafe_allow_html=True)

        st.info(
            'Our AI Personalization streams, a product of this collaboration, aims to transform gaming from a one-size-fits-all model to an experience tailored to individual players’ tastes. To achieve this, we created the OptX-AI system, a pioneering real-time recommender system.')

        icon_size = 20

        st_button('youtube', 'https://www.youtube.com/@leepand', 'Leepand', icon_size)
        st_button('github', 'https://github.com/leepand/', 'AlogLink GitHub', icon_size)
        # st_button('twitter', 'https://twitter.com/andrejusb', 'Follow me on Twitter', icon_size)
        # st_button('medium', 'https://andrejusb.medium.com', 'Read my Blogs on Medium', icon_size)
        #st_button('linkedin', 'https://www.linkedin.com/in/andrej-baranovskij/', 'Follow me on LinkedIn', icon_size)
        st_button('', 'https://algolink.io', 'AlogLink ML', icon_size)