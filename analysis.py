import matplotlib.pyplot as plt
import numpy as np
import string

from collections import Counter
from wordcloud import WordCloud


with open('scraped.txt', 'r') as f:
    lines = [url.strip() for url in f.readlines()]

urls = [
    line
        # grab url
        .split(', ', 3)[3]
        # strip trailing slash
        .rstrip('/')
        # now strip everything before the last slash
        .rsplit('/', 1)[1]
        # remove fragments, queries, and percent encoding, etc.
        .split('#')[0]
        .split('?')[0]
        .split('%')[0]
        .split('-')
        
    for line in lines
    # filter out lines that don't have a dash (i.e., no slug)
    if '-' in line
]

# flatten list
words = np.hstack(urls)
words = [
    word
    for word in words
    # filter out words that contain digits
    if all(c not in word for c in string.digits)

]

frequency_dict = Counter(words)

wc = WordCloud(background_color="white", max_words=1000)
wc.generate_from_frequencies(frequency_dict)

plt.imshow(wc, interpolation="bilinear")
plt.axis("off")
plt.show()
