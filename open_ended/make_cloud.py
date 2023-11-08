import matplotlib.pyplot as plt
import numpy as np

from collections import Counter
from wordcloud import WordCloud

with open('data.csv', 'r', encoding="utf-8-sig") as f:
    lines = [l.strip().split(',') for l in f.readlines()]

raw_titles = [i[0].split(" | ")[0] for i in lines[1:]] #Remove authors from title
filter_titles = [i.replace("’", "").replace("‘", "").replace("–","").replace("\'s", "").replace(":", "") for i in raw_titles] #Remove special characters for consistent tokenisation of words

words_words = [word.split() for word in filter_titles] #Split title into individual words
words_token = [token.lower() for words in words_words for token in words] #Convert all words to lowercase for consistent tokenisation
general_words = ("the", "for", "on", "in", "to", "as", "a", "and", "of", "from", "at", "is", "by", "not", "be", "with", "what", "are", "it") #Tuple of common Grammatical Terms
words_token_filtered = list(filter(lambda x: x not in general_words, words_token)) #Remove common grammar tokens to improve visualisation

frequency_dict = Counter(words_token_filtered) #Frequency count of tokens

#Generate wordcloud with WordCloud library
wc = WordCloud(background_color="white", max_words=1000, width=800, height=400)
wc.generate_from_frequencies(frequency_dict)

#plt to save wordcloud as image
plt.figure(figsize=(12, 6))
plt.imshow(wc, interpolation="bilinear")
plt.axis("off")
plt.savefig("fig.png", dpi=300)
plt.show()
