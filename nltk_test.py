from nltk.tokenize import sent_tokenize

text = (
    "Hi, Mr. Owen. I'm Naoki Shimoda working at PKSHA Technology Inc. in Tokyo."
    "This is the first sentence. Here's the second one! Is this the third? Yes, it is."
)
sentences = sent_tokenize(text)
print(text)
print(sentences)
