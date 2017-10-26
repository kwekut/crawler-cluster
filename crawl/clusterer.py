from __future__ import absolute_import
import numpy as np
import pandas as pd
import nltk
import re
import os
import codecs
import uuid
import json
from datetime import datetime
from sklearn import feature_extraction
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.cluster.hierarchy import ward, dendrogram, linkage, cophenet, fcluster
from scipy.spatial.distance import pdist
from collections import defaultdict
import matplotlib
import matplotlib as mpl
#import mpld3
import language_check
from nltk.stem.snowball import SnowballStemmer
# from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from elasticsearch import Elasticsearch
matplotlib.use('Agg')
import matplotlib.pyplot as plt
tool = language_check.LanguageTool('en-US')
# elasticClient = Elasticsearch(
#     ['elastic-node1'], port=9200
# )
# elasticClient.indices.create(index='stories', ignore=400)
# nltk.download('popular')
# nltk.download('punkt')

# @app.task(bind=True,default_retry_delay=10) # set a retry delay, 10 equal to 10s
def start_clustering(batchid,data,topics,uris,publishers):
    #input data and topics [(publisher, newUrl, newTopic)]
    # stopWords = stopwords.words('english')
    stemmer = SnowballStemmer("english")

    def tokenize_and_stem(text):
        tokens = [word for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]
        filtered_tokens = []
        for token in tokens:
            if re.search('[a-zA-Z]', token):
                filtered_tokens.append(token)
        stems = [stemmer.stem(t) for t in filtered_tokens]
        return stems


    def tokenize_only(text):
        tokens = [word.lower() for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]
        filtered_tokens = []
        for token in tokens:
            if re.search('[a-zA-Z]', token):
                filtered_tokens.append(token)
        return filtered_tokens


    totalvocab_stemmed = []
    totalvocab_tokenized = []
    finalKeywords = []
    for publisher,category,url,topic,image in data:
        allwords_stemmed = tokenize_and_stem(str(topic)) #for each item in 'data', tokenize/stem
        totalvocab_stemmed.extend(allwords_stemmed) #extend the 'totalvocab_stemmed' list
        
        allwords_tokenized = tokenize_only(str(topic))
        totalvocab_tokenized.extend(allwords_tokenized)
        finalKeywords.append(allwords_tokenized)

    vocab_frame = pd.DataFrame({'words': totalvocab_tokenized}, index = totalvocab_stemmed)
    tfidf_vectorizer = TfidfVectorizer(max_df=1.0, max_features=200000,
                                     min_df=1, stop_words='english',
                                     use_idf=True, tokenizer=tokenize_and_stem, ngram_range=(1,3))
    #Returns - sparse matrix, [n_samples, n_features]
    tfidf_matrix  = tfidf_vectorizer.fit_transform(topics)
    terms = tfidf_vectorizer.get_feature_names()
    X = 1 - cosine_similarity(tfidf_matrix)

    #The input y may be either a 1d compressed distance matrix or a 2d array of observation vectors
    #https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.linkage.html#scipy.cluster.hierarchy.linkage
    #Z = linkage(X, 'ward')
    linkage_matrix = ward(X)

    # The closer the value is to 1, the better the clustering preserves the original distances
    #c, coph_dists = cophenet(Z, pdist(X))
    fig, ax = plt.subplots(figsize=(15, 20)) # set size
    ax = dendrogram(linkage_matrix, orientation="right", labels=publishers);
    plt.tick_params(\
        axis= 'x',          # changes apply to the x-axis
        which='both',      # both major and minor ticks are affected
        bottom='off',      # ticks along the bottom edge are off
        top='off',         # ticks along the top edge are off
        labelbottom='off')

    plt.tight_layout() 
    plt.savefig('ward_clusters.png', dpi=200) #save figure as ward_clusters
    # plt.show()
    #https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.cluster.hierarchy.fcluster.html
    clusters = fcluster(linkage_matrix, 8, criterion='maxclust', depth=10)
    documentsMap = defaultdict(list)
    for idx, grp in enumerate(clusters):
        pb,ct,ur,tp,im = data[idx]
        gp = str(grp)
        cdoc = (gp,ct,pb,finalKeywords[idx],tp,ur,im)
        documentsMap[gp].append(cdoc)
    #create parent for group
    #parent's publisher,keywords,topics are accumulation of all childs
    #nest update children
    models = []
    today = str(datetime.date.today())
    for grp in documentsMap:
        pdoc = defaultdict(str)
        children = []
        pdoc['children'] = str(children)
        parentid = str(uuid.uuid4())
        pdoc['_op_type'] = 'index'
        pdoc['_index'] = 'stories'
        pdoc['_type'] = today
        pdoc['_id'] = parentid
        pdoc['parentid'] = parentid
        pdoc['created'] = str(datetime.now())
        pdoc['batchid'] = batchid
        pdoc['groupid'] = grp + batchid
        pdoc['group'] = grp
        for gp,ct,pb,kw,tp,ur,im in documentsMap.get(grp):
            # pdoc['title'] = language_check.correct( str(tp), tool.check(str(tp)) )
            pdoc['category'] += str(ct) + ", "
            pdoc['publisher'] += str(pb) + ", "
            pdoc['keywords'] += str(kw) + ", "
            pdoc['topic'] += str(tp) + " ... "
            pdoc['url'] += str(ur) + ", "
            pdoc['image'] += str(im) + ", "
            children.append ( {'group':gp,'category':ct,'publisher':pb,'keywords':kw,'topic':tp,'url':ur,'image':im} )
        models.append(json.dumps(pdoc))
        # Elasticsearch.helpers.bulk(elasticClient, models, stats_only=False, **kwargs)
        # Elasticsearch.helpers.parallel_bulk(elasticClient,models, thread_count=4, chunk_size=500, max_chunk_bytes=104857600, queue_size=4, **kwargs)
    return models

