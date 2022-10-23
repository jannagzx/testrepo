from abc import abstractmethod
import os
import numpy as np
import requests
import re
import sys
import argparse
import newspaper
import nltk
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import logging



class TextFormatter():
    def __init__(self, format_settings):
        if format_settings == {}:
            pass
        
    def format(self, text):
        text = text.lower()
        text = self._remove_numbers(text)
        text = self._remove_punctuation(text)
        text = self._normalize(text)
        # text = self._remove_stop_words(text)
        return text
        
    def _remove_numbers(self, text):
        return re.sub(r'\d+','',text)
        
    def _remove_stop_words(self, text):
        stop_words = set(stopwords.words('english'))
        no_stpwords_text=""
        for i in text.split():
            if not i in stop_words:
                no_stpwords_text += i+' '
        return no_stpwords_text
        
    def _remove_punctuation(self, text):
        return re.sub(r'[^\w\s]','', text)
        
    def _normalize(self, text):
        return text

    def stemming(self, text):
        return text
        
    def lemmatize(self, text):
        return text
        
class NewsAccessBase():
    def __init__(self, location):
        self._location = location
    
    @abstractmethod
    def save(self, news):
        raise NotImplementedError

    @abstractmethod
    def read(self):
        raise NotImplementedError
        

class AccessTxtFiles(NewsAccessBase):
    def save(self, news, topic, count):
        file_name = str(count)+'.txt'
        try:
            os.makedirs(os.path.join(self._location, topic))
        except:
            pass
        location = os.path.join(self._location, topic, file_name)
        with open(location, 'w') as f:
            f.write(news)
            
    def read(self, location):
        with open(location, 'r') as f:
            return f.read()


class NewsAccess():
    def __init__(self, _type, location):
        self._type = _type
        self._location = location
        self._article_count = {}
        if _type == 'text':
            self._accessor = AccessTxtFiles(location)
        else:
            raise "This type of saver is not defined."
            
    def save(self, news_article, topic):
        if topic not in self._article_count:
            self._article_count[topic] = 0
        if self._article_count[topic] > 10:
            pass
        else:
            self._article_count[topic] += 1
            self._accessor.save(news_article, topic, self._article_count[topic])
            logging.info(f"saved article number self._article_count[topic] for the topic {topic}.")
        return self._article_count[topic]

    def read_articles(self, topic):
        for i in range(self._article_count[topic]):
            article_number = i+1
            file_name = str(article_number)+'.txt'
            location = os.path.join(self._location, topic, file_name)
            yield self._accessor.read(location)
            
    
    
class NewsScrapperBase():
    def __init__(self, url, location, format_settings={}):
        self._url = url
        self._location = location
        self._formatter = TextFormatter(format_settings)
    
    @abstractmethod
    def scrape_news(self, topic):
        raise NotImplementedError


class NewspaperArticlesScrapper(NewsScrapperBase):
    
    def _scan_for_relevant_topic(self, topic, article):
        if topic in article.lower():
            return True
        else:
            return False
    
    def _process_article(self, article, topic, accessor):
        num_saved_articles = 0
        try:
            article.download()
        except:
            pass
        article.parse()
        text = article.text
        if self._scan_for_relevant_topic(topic, text):
            formatted_text = self._formatter.format(text) 
            num_saved_articles = accessor.save(formatted_text, topic)
        return num_saved_articles
            
    def scrape_news(self, topic, accessor):
        self._site = newspaper.build(self._url, memoize_articles=False)  
        self._site.article_urls()
        for article in self._site.articles:
            num_saved_articles = self._process_article(article, topic, accessor)
            if num_saved_articles > 10:
                break

class Sentiment_Analyzer():
    def __init__(self, accessor):
        self._accessor = accessor
        self._scores = []
        
    def analyze_article(self, article):
        sid = SentimentIntensityAnalyzer()
        polarity_scores = sid.polarity_scores(article)
        return polarity_scores['compound']
    
    def analyze_overall_sentiment(self, topic):
        for article in self._accessor.read_articles(topic):
            self._scores.append(self.analyze_article(article))
        print(f"Overall Sentiment score is {sum(self._scores) / len(self._scores)}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--location", default="/Users/mukund/Documents/python projects/news articles")
    parser.add_argument("-u", "--url", default="https://www.nbcnews.com/world")
    args = parser.parse_args()
    location = args.location
    url = args.url
    
    articles_scrapper = NewspaperArticlesScrapper(url, location)
    accessor = NewsAccess(_type="text", location=location)
    sentiment_analyzer = Sentiment_Analyzer(accessor)
    
    while True:
        topic = input("Input your topic of interest. Type q to quit:  ")
        topic = topic.lower()
        if topic == 'q':
            break
        articles_scrapper.scrape_news(topic, accessor)
        sentiment_analyzer.analyze_overall_sentiment(topic)


if __name__ == "__main__":
    main()