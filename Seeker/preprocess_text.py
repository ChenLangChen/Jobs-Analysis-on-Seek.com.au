"""This script aims at prerpocessing a piece of text, then find the most frequent words"""
# Import data cleaning libraries
import string
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
nltk.download('stopwords')
from collections import Counter
import re
from gensim.models import Phrases
import re
#########################################
def list_to_str (token_list):
    "Function to append all tokens into a string"
    my_str = ""
    for item in token_list:
        my_str = my_str + item + " "
    return my_str


def my_remove_punctuation(my_str):
    "Function to remove punctuations, and replace them with space. It helps tokenize words like SQL/MySql"
    regex = re.compile('[%s]' % re.escape(string.punctuation))
    out = regex.sub(' ', my_str)
    return out


def multi_word_tokenize(bigram, test_text):
    tokenized_words = bigram[test_text.split()]
    new_list = list()
    for item in tokenized_words:
        new_item = item.replace("_"," ")
        new_list.append(new_item)
    return new_list



# Remove stopwords function
def remove_stopwords(text):
    stop_words = set(stopwords.words("english"))
    # Adding some extra customised stop_words, removing some word too generic
    # extra_words=['us','within','want','best', 'work', 'help', 'part', 'opportunity', 'across', 'working',
    #              'meet','ltd']
    # for item in extra_words:
    #     stop_words.add(item)

    filtered_text = [word for word in text if word not in stop_words]
    return filtered_text

# Remove punctuation
def remove_punctuation (text):
  return re.sub(r'[^\w\s]','',text)

# Remove non alphabetic characters
def remove_non_alphabet (text):
  return [word for word in text if (word.isalpha())]
###########################################################

def filter_generic_words(text):
    "Function to filter out words are too generic for my purpose, similar to wordcloud"
    stop_words = set()
    extra_words=['us','within','want','best', 'work', 'help', 'part', 'opportunity', 'across', 'working',
                 'meet','ltd','using','world','great things']
    for item in extra_words:
        stop_words.add(item)
    filtered_text = [word for word in text if word not in stop_words]
    return filtered_text

###########################################################

def my_tokenizer(text):
    "Customised tokenizer"
    return re.split(' |,|;|/', text)

###########################################################
# Combine all of the methods above to clean the data

def get_bigram(train_corpus):
    # train_corpus is a list of sentences(str)
    sentence_stream = [doc.split(" ") for doc in train_corpus]
    bigram = Phrases(sentence_stream, min_count=3, threshold=5)
    "min_count : ignore all words and bigrams with total collected count lower than. Default is 5"
    "threshold: threshold for forming the phrase. Default is 10, the higher, the fewer phrases"
    return bigram


def clean_str(bigram, line):
  # Remove punctuations
  new_line = my_remove_punctuation(line.lower())
  # Tokenize the line
  new_line = word_tokenize(new_line)
  # Remove non-alphabetic words
  new_line = remove_non_alphabet(new_line)
  # Remove stopwords
  new_line = remove_stopwords(new_line)

  new_line = list_to_str(new_line)
  new_line = multi_word_tokenize(bigram, new_line)
  new_line = filter_generic_words(new_line)

  return new_line



"""🌥🌪🌬🌊I need to combine and create one function: Given a job_description, return the most frequent words """
def get_frequent_words(train_corpus, text_str, top_num):
    "Function to return the most frequent words from a text"
    cleaned_text = clean_str(train_corpus, text_str)
    counter_obj = Counter(cleaned_text)
    most_occur = counter_obj.most_common(top_num)
    return most_occur


#
