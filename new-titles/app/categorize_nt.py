from app.data.ref.train import train
import random
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.naive_bayes import MultinomialNB

from nltk.corpus import stopwords
stops = stopwords.words('english') + stopwords.words('german') + stopwords.words('french')

def preprocess(text):
    punctuation ="\"#$%&\'()*+,-/:;<=>@[\]^_`{|}~.?!"
    translator = str.maketrans({key: " " for key in punctuation})
    text = text.translate(translator)

    symbols = "©"
    translator = str.maketrans({key: " " for key in symbols})
    text = text.translate(translator)

    translator = str.maketrans({key: " " for key in '0123456789'})
    text = text.translate(translator)

    return text

data_ = [item for item in train]
data_ = random.sample(data_, len(data_))
train_data = [preprocess(item[1]) for item in data_][:2000]
train_target = [item[0] for item in data_][:2000]
test_data = [preprocess(item[1]) for item in data_][2000:]
test_target = [item[0] for item in data_][2000:]

categories = set([item[0] for item in train])

def predict_categories(titles):
    count_vect = CountVectorizer(stop_words=stops, min_df=5)
    X_train_counts = count_vect.fit_transform(train_data)
    tfidf_transformer = TfidfTransformer()
    X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)
    clf = MultinomialNB().fit(X_train_tfidf, train_target)
    X_new_counts = count_vect.transform(titles)
    X_new_tfidf = tfidf_transformer.transform(X_new_counts)
    predicted = clf.predict(X_new_tfidf)
    return predicted
