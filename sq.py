import streamlit as st
from openai import OpenAI
import PyPDF2
import docx

class OllamaInit:
    def __init__(self):
        self.client = OpenAI(
            api_key="ollama",
            base_url="http://localhost:11434/v1/"
        )
        self.model="deepseek-r1:7b"

    def extract_file(self, upload_file):
        text = ""
        if upload_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(upload_file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        elif (
            upload_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            doc = docx.Document(upload_file)
            for params in doc.paragraphs:
                text += params.text + "\n"
        else:
            text = str(upload_file.read(), "utf-8")

        return text

    def analyze_context(self, text, query):
        prompt = f"""Analyze this text and answer the following query:
            Text: {text[:2000]}...
            Query: {query}
            
            Provide:
            1. Direct answer to the query
            2. Supporting evidence
            3. Key findings
            4. Limitations of the analysis
            """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a research assistant skilled in analyzing academic and technical documents and don't include chinese characters"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                stream=True
            )

            result = st.empty()
            collected_chunks = []

            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    collected_chunks.append(chunk.choices[0].delta.content)
                    result.markdown("".join(collected_chunks))
            
            return "".join(collected_chunks)

        except Exception as e:
            return f"An error occurred: {str(e)}"



def main():
    st.set_page_config(page_title="Ollama", layout="wide")
    st.title("Summarization Assistant")

    assistant = OllamaInit()

    # Sidebar for document upload
    with st.sidebar:
        st.header("Upload Document")
        upload_files = st.file_uploader(
            "Upload research documents",
            type = ["pdf", "docx", "txt"],
            accept_multiple_files=True
        )

    # main content area
    if upload_files:
        st.write(f"{len(upload_files)} files uploaded")

        query = st.text_area(
            "Enter your query here",
            placeholder="What is the impact of climate change on agriculture?",
            height=100
        )

        if st.button("Analyze"):
            with st.spinner("Analyzing..."):
                for file in upload_files:
                    st.write(f"### analysis of {file.name}")
                    text = assistant.extract_file(file)


                    #create tabs for different analyses
                    tab1, tab2, tab3 = st.tabs(
                        ["main analysis", "key points", "summary"]
                    )

                    with tab1:
                        assistant.analyze_context(text, query)

                    with tab2:
                        assistant.analyze_context(text, "Extract key points and findings")
                    
                    with tab3:
                        assistant.analyze_context(text, "Summarize the document")

                if len(upload_files) > 1:
                    st.write("### Cross-Document Analysis")
                    st.write("Comparing findings across documents...")
                    # Add comparison logic here

if __name__ == "__main__":
    main()

