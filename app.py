import streamlit as st
import os
import pandas as pd
import numpy as np
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import io
import docx2txt
import spacy
from spacy.matcher import Matcher
import re
from collections import defaultdict
from nltk.corpus import stopwords
import sys
import nltk
from stqdm import stqdm
from random import randint

nltk.download('stopwords')
# load pre-trained model
nlp = spacy.load('en_core_web_sm')

# initialize matcher with a vocab
matcher = Matcher(nlp.vocab)
matcher_3 = Matcher(nlp.vocab)

### Defining Stopwords ###
temp_df = pd.read_csv('./data/skills.csv')
name_stopwords = stopwords.words('english')
name_stopwords.extend(temp_df['Skills'].to_list())
# From Africa Folder
name_stopwords.extend(['adobe','xd','national','development','none','workedwithotherteam','Membersingatheringrequirementsfor','Oni','Street','Hu','Mobile','docx','pdf','cv'])
name_stopwords = [x.lower() for x in name_stopwords]


st.set_page_config(page_title="Resume Extractor", page_icon=":tired:", layout="wide")

# -- Header Section --
with st.container():
    st.title("Resume Parser :page_facing_up:")

# Extract PDF Function
def extract_text_from_pdf(pdf_path):
    # with open(pdf_path, 'rb') as fh:
        # iterate over all pages of PDF document
    for page in PDFPage.get_pages(pdf_path, caching=True, check_extractable=True):
            # creating a resoure manager
        resource_manager = PDFResourceManager()
            
            # create a file handle
        fake_file_handle = io.StringIO()
            
            # creating a text converter object
        converter = TextConverter(
                                resource_manager, 
                                fake_file_handle, 
                                codec='utf-8', 
                                laparams=LAParams()
                    )

            # creating a page interpreter
        page_interpreter = PDFPageInterpreter(
                                resource_manager, 
                                converter
                        )

            # process current page
        page_interpreter.process_page(page)
            
            # extract text
        text = fake_file_handle.getvalue()
        yield text

            # close open handles
        converter.close()
        fake_file_handle.close()

# Extract Word Document Function
def extract_text_from_doc(doc_path):
    temp = docx2txt.process(doc_path)
    text = [line.replace('\t', ' ') for line in temp.split('\n') if line]
    return ' '.join(text)

### Name Functions ###
def extract_name(resume_text):
    nlp_text = nlp(resume_text)
    
    # First name and Last name are always Proper Nouns
    pattern = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]
    
    matcher.add('NAME', [pattern])
    
    matches = matcher(nlp_text)
    
    for match_id, start, end in matches:
        span = nlp_text[start:end]
        return span.text
    
def extract_name_3(resume_text):
    nlp_text = nlp(resume_text.lower())
    
    # First name and Last name are always Proper Nouns
    pattern = [{'POS': 'PROPN'},{'POS': 'PROPN'},{'POS': 'PROPN'}]
    
    matcher_3.add('NAME', [pattern])
    matches = matcher_3(nlp_text)
    
    for match_id, start, end in matches:
        span = nlp_text[start:end]
        return span.text

def check_name(name_text):
    try:
        name = []
        if len(set(re.findall(r'\w+',extract_name(name_text))).intersection(set(re.findall(r'\w+',extract_name_3(name_text))))) == 2:
            name_list = re.findall(r'\w+',extract_name_3(name_text))
        else:
            name_list = re.findall(r'\w+',extract_name(name_text))
        for word in name_list:
            if word not in name_stopwords:
                name.append(word.capitalize())
        name = " ".join(name)
        return name
    except:
        try:
            return(" ".join(word for word in re.findall(r'\w+',extract_name(name_text)) if word not in name_stopwords).capitalize())
        except:
            return None
    
# Extract Phone Numbers
def extract_africa_mobile_number(text):
    phone = re.findall("\+?[\d\s]{9,20}", text)
    if phone:
        for item in phone:
            if len(item.strip()) > 9:
                phone = item.strip()
                break
            else:
                pass

        if phone and type(phone) == str:
            return phone
        else:
            return None
    else:
        return None
    
# Extract Email - Regex
def extract_email(email):
    email = re.findall("([^@|\s]+@[^@]+\.[^@|\s]+)", email)
    if email:
        try:
            return email[0].split()[0].strip(';')
        except IndexError:
            return None
# Extract Skills - Skills are Manually extracted and put into a csv file which is included in the repo
def extract_skills(resume_text):
    nlp_text = nlp(resume_text)

    # removing stop words and implementing word tokenization
    tokens = [token.text for token in nlp_text if not token.is_stop]

    # reading the csv file
    data = pd.read_csv("./data/skills.csv",index_col=False)
    data = data.set_index('Skills')
    data = data.transpose()
    
    # extract values
    skills = list(data.columns.values)
    a = (map(lambda x: x.lower(), skills))
    skills = list(a)
    
    skillset = []
    
    # check for one-grams (example: python)
    for token in tokens:
        if token.lower() in skills:
            skillset.append(token)
            
    
    # check for bi-grams and tri-grams (example: machine learning)
    for token in nlp_text.noun_chunks:
        token = token.text.lower().strip()
        if token in skills:
            skillset.append(token)
    
    return [i.capitalize() for i in set([i.lower() for i in skillset])]

# key skills extraction
def find_skills(x):
    return list(dict.fromkeys(x))

# Merging Data
def mergeDictionary(d1, d2):
    d = {}

    for key in set(list(d1.keys()) + list(d2.keys())):
        try:
            d.setdefault(key,[]).append(d1[key])        
        except KeyError:
            pass

        try:
            d.setdefault(key,[]).append(d2[key])          
        except KeyError:
            pass
    return d

# Education
STOPWORDS = set(stopwords.words('english'))

# Education Degrees
EDUCATION = [
            'B.E.','B.E',
            'BS','B.S',
            'B.SC','B.SC.','BSC',
            'M.E', 'M.E.', 'MS', 'M.S', 
            'BTECH', 'B.TECH', 'M.TECH', 'MTECH', 
            'SSC', 'HSC', 'CBSE', 'ICSE', 
            # 'X', 'XII',
            'BACHELOR','DIPLOMA'
            ]

def extract_education(resume_text):
    nlp_text = nlp(resume_text)
    # extended_stopwords = STOPWORDS.append(['me','be'])

    # Sentence Tokenizer
    nlp_text = [sent.text.strip() for sent in nlp_text.sents]

    edu = {}
    # Extract education degree
    for index, text in enumerate(nlp_text):
        for tex in text.split():
            # Replace all special symbols
            tex = re.sub(r'[?|$|.|!|,]', r'', tex)
            if tex.upper() in EDUCATION and tex not in STOPWORDS:
                # edu[tex] = text
                if tex in nlp_text[index]:   
                    keyword = tex
                    before_keyword, keyword, after_keyword = nlp_text[index].partition(keyword)
                    edu[tex] = (keyword + after_keyword).replace("\n"," ")
    if edu:
        return edu
    else:
        pass

with st.container():
    def single_extraction(file):
        if file.name.endswith('pdf') or file.name.endswith('docx'):
            name_list = []
            phone_list = []
            email_list = []
            skill_list = []
            education_list = []
                # If PDF or DOCX, call functions and append data into list to put into dataframe later
            if file.name.endswith('pdf'):
                for page in extract_text_from_pdf(file):
                    name_list.append(check_name(extract_name(page.lower())))
                    phone_list.append(extract_africa_mobile_number(page))
                    email_list.append(extract_email(page))
                    skill_list.extend(extract_skills(page.lower()))
                    education_list.append(extract_education(page))
            elif file.name.endswith('docx'):
                doc_file = extract_text_from_doc(file)
                name_list.append(check_name(extract_name(doc_file.lower())))
                phone_list.append(extract_africa_mobile_number(doc_file))
                email_list.append(extract_email(doc_file))
                skill_list.extend(extract_skills(doc_file.lower()))
                education_list.append(extract_education(doc_file))

        ######### Filtering conditions###################
                # Name
            if name_list != None:
                name = name_list[0]
            else:
                name = None
                # Phone
            if phone_list != None:
                number = phone_list[0]
            else:
                number = None
                # Email
            if email_list != None:
                email = email_list[0]
            else:
                email = None
                # Education
            if education_list != None:
                education = education_list[0]
            else:
                education = None
            skill_list = find_skills(skill_list)
        ##################################################      
                # collate into a dictionary
            temp_cv = {
                    'Name': [name],
                    'Phone':[number],
                    'Email': [email],
                    'Skills':[skill_list],
                    'Education':[education]
            }
            df = pd.DataFrame(temp_cv)
            return(df)
        # except Exception:
        #     print('Data encountered an error')
        #     pass
    st.write('---')
    if 'key' not in st.session_state:
        st.session_state.key = str(randint(1000, 100000000))
    uploaded_files = st.file_uploader("Choose a file (Only pdf and docx formats accepted)",type=['pdf','docx'], key=st.session_state.key, accept_multiple_files=True)
    if uploaded_files is not None:
        # file_details = {'filename':uploaded_file.name, 'filetype':uploaded_file.type}
        # st.write(file_details)

        df = pd.DataFrame({'Name':[],'Phone':[],'Email':[],'Skills':[], 'Education':[]})
        for uploaded_file, percent_complete in zip(uploaded_files,stqdm(range(len(uploaded_files)))):
            df = pd.concat([df,single_extraction(uploaded_file)],ignore_index=True)
        st.table(df)
    if st.button('Clear Uploaded File(s)') and 'key' in st.session_state.keys():
        st.session_state.pop('key')
        st.experimental_rerun()

    @st.cache
    def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')

    csv = convert_df(df)

    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='resume_data.csv',
        mime='text/csv',
    )
