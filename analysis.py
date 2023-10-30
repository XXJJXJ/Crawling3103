from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np
import string
from collections import Counter

with open('scraped.txt', 'r') as f:
    lines = [url.strip() for url in f.readlines()]

urls = [
    line
        .split(', ', 3)[3]
        .rstrip('/')
        .rsplit('/', 1)[1]
        .split('#')[0]
        .split('?')[0]
        .split('%')[0]
        .split('-')
        
    for line in lines
    if
        '-' in line
    ]
words = np.hstack(urls)
words = [
    word
    for word in words
    if
        all(c not in word for c in string.digits)

]

frequency_dict = Counter(words)

def makeImage(frequency_dict):
    wc = WordCloud(background_color="white", max_words=1000)
    wc.generate_from_frequencies(frequency_dict)

    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.show()



makeImage(frequency_dict)