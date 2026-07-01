# -*- coding: utf-8 -*-
import cPickle
import numpy as np
import pandas as pd
import datetime,time
import calendar,json
import random, os, re
import collections
import math, glob
from scipy import stats
import scipy
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import math, cPickle
import collections, scipy
from scipy.stats import norm, truncnorm
from scipy.stats.mstats import gmean
import matplotlib.gridspec as gridspec
from matplotlib.pyplot import gca
import seaborn.apionly as sns
from scipy import optimize 
from matplotlib.ticker import NullFormatter
import operator as op


    
plt.style.use('seaborn-ticks')
from matplotlib import rcParams
rcParams['figure.figsize'] = (5, 5)

matplotlib.rcParams['xtick.labelsize'] = 18
matplotlib.rcParams['ytick.labelsize'] = 18
matplotlib.rcParams['font.size'] = 18
matplotlib.rcParams['xtick.direction'] = 'in'
matplotlib.rcParams['ytick.direction'] = 'in'
matplotlib.rcParams['xtick.top'] = 'True'
matplotlib.rcParams['ytick.right'] = 'True'
hfont = {'fontname':'Helvetica'} 

def calculate_period_length(lists, thr):
    dd = lists
    new = []
    a = thr
    for i in dd:
        if i>=a:
            y = 1
        else:
            y = 0
        new.append(y)
    new =  max(np.array(list(count_consequtive_items(new)))[:, 1])
    return new

def count_consequtive_items(lst, exclude=[0], reset_after_pass=True):
    """
    return the length of consecutive non-zero values in a list
    """
    prev = None
    count = 0
    for item in lst:
        if item in exclude:
            if prev and count:
                yield prev, count
            if reset_after_pass:
                prev = None
                count = 0
            continue
        if item != prev and count:
            yield prev, count
            count = 0
        count += 1
        prev = item
    if prev and count:
        yield prev, count
        
        
def shuffle_same_year(data):
    """
    input: (impact, year)
    output: randomize the order of movies in the same year
    """
    shuffle_data = []
    data = list(data)
    year   = sorted(list(set([i[-1] for i in data])))
    for y in year:
        sub_data = [i for i in data if i[-1] == y]
        shuffle_subdata = random.sample(sub_data, len(sub_data))
        shuffle_data += shuffle_subdata

    return np.array(shuffle_data)

def load_data(filepath, domain):
    """
    read impact sequence from txt file 
    """
    data = []
    with open(filepath) as f:
        for line in f:
            rec = [i.split(',') for i in line.split('|')]
            rec = np.array([[float(i) for i in j] for j in rec])
            data.append(rec)

    return data

def calculate_N_order(list_of_list, domain):
    order_1 = []
    order_2 = []
    order_3 = []
    shuffle_order_1 = []
    shuffle_order_2 = []
    shuffle_order_3 = []
    if domain == 'sci':
        for rec in list_of_list:
            y = np.array([j[1] for j in rec])
            sort_y = sorted(list(set(y)))
            if len(sort_y)>=3:
                o1 = np.where(y == sort_y[-1])[0]
                o2 = np.where(y == sort_y[-2])[0]
                o3 = np.where(y == sort_y[-3])[0]

                o1 = random.sample(o1, 1)[0]
                o2 = random.sample(o2, 1)[0]
                o3 = random.sample(o3, 1)[0]
                order_1+=[(o1+0.5)*1.0/len(y)]
                order_2+=[(o2+0.5)*1.0/len(y)]
                order_3+=[(o3+0.5)*1.0/len(y)]
                
            new_y = random.sample(y, len(y))
            if len(sort_y)>=3:
                o1 = np.where(new_y == sort_y[-1])[0]
                o2 = np.where(new_y == sort_y[-2])[0]
                o3 = np.where(new_y == sort_y[-3])[0]

                o1 = random.sample(o1, 1)[0]
                o2 = random.sample(o2, 1)[0]
                o3 = random.sample(o3, 1)[0]
                shuffle_order_1+=[(o1+0.5)*1.0/len(y)]
                shuffle_order_2+=[(o2+0.5)*1.0/len(y)]
                shuffle_order_3+=[(o3+0.5)*1.0/len(y)]
    
    elif domain == 'art':
        for rec in list_of_list:
            y = np.array(rec)[:, 0]
            sort_y = sorted(list(y))
            if len(sort_y)>=3:
                o1 = np.where(y == sort_y[-1])[0]
                o2 = np.where(y == sort_y[-2])[0]
                o3 = np.where(y == sort_y[-3])[0]

                o1 = random.sample(o1, 1)[0]
                o2 = random.sample(o2, 1)[0]
                o3 = random.sample(o3, 1)[0]
                order_1+=[(o1+0.5)*1.0/len(y)]
                order_2+=[(o2+0.5)*1.0/len(y)]
                order_3+=[(o3+0.5)*1.0/len(y)]
                
            new_y = random.sample(y, len(y))
            if len(sort_y)>=3:
                o1 = np.where(new_y == sort_y[-1])[0]
                o2 = np.where(new_y == sort_y[-2])[0]
                o3 = np.where(new_y == sort_y[-3])[0]

                o1 = random.sample(o1, 1)[0]
                o2 = random.sample(o2, 1)[0]
                o3 = random.sample(o3, 1)[0]
                shuffle_order_1+=[(o1+0.5)*1.0/len(y)]
                shuffle_order_2+=[(o2+0.5)*1.0/len(y)]
                shuffle_order_3+=[(o3+0.5)*1.0/len(y)]

    elif domain == 'dir':
        for rec in list_of_list:
            y = np.array(rec)[:, 0]
            sort_y = sorted(zip(y, range(len(y))), key = lambda x:x[0])
            orders = np.array(sort_y[:3])
            if set(orders[:, 0])<3:
                orders = random.sample(orders, len(orders))
            o1 = orders[2][-1]
            o2 = orders[1][-1]
            o3 = orders[0][-1]
            
            order_1+=[(o1+0.5)*1.0/len(y)]
            order_2+=[(o2+0.5)*1.0/len(y)]
            order_3+=[(o3+0.5)*1.0/len(y)]
                
            
            new_y = random.sample(y, len(y))
            #if len(sort_y)>=3:
            o1 = np.where(new_y == sort_y[-1])[0]
            o2 = np.where(new_y == sort_y[-2])[0]
            o3 = np.where(new_y == sort_y[-3])[0]

            o1 = random.sample(o1, 1)[0]
            o2 = random.sample(o2, 1)[0]
            o3 = random.sample(o3, 1)[0]
            shuffle_order_1+=[(o1+0.5)*1.0/len(y)]
            shuffle_order_2+=[(o2+0.5)*1.0/len(y)]
            shuffle_order_3+=[(o3+0.5)*1.0/len(y)]
            
    return order_1, order_2, order_3, shuffle_order_1, shuffle_order_2, shuffle_order_3
        

def calculate_phi(list1, list2):
    delta_x = 0.1
    bins = np.arange(0, 1+delta_x, delta_x)
    hist = np.histogram2d(list1, list2, bins=bins, normed = 'sample_count')

    hist_x, x = np.histogram(list1, bins = hist[1], density = True)
    hist_y, y = np.histogram(list2, bins = hist[2], density = True)
    reverse_h = []
    for i in range(len(hist[0])):
        new = [hist[0][i][j]/hist_x[j]/hist_y[i] for j in range(len(hist[0][i]))]
        #new = hist[0][i]
        reverse_h = [new] + reverse_h
    reverse_h = np.array(reverse_h)

    fig = plt.figure(figsize = (6,6))
    ax = fig.add_axes([0.3, 0.3, 0.5, 0.5]) 
    sns.heatmap(reverse_h, cmap="bwr", vmin = 0.0, vmax = 2.2, center = 1.1, cbar = True, xticklabels = x[:-1], yticklabels = sorted(y[:-1], reverse = True))

def calculate_R(list1, list2, shuffle1, shuffle2, bins):
    fig = plt.figure(figsize = (6,6))
    ax = fig.add_axes([0.3, 0.3, 0.5, 0.5])
    hist, x = np.histogram(np.array(list1)-np.array(list2), bins = bins, density = True)
    hist_r, x = np.histogram(np.array(shuffle1)-np.array(shuffle2), bins = bins, density = True)
    xx = (x[1:]+x[:-1])/2.0
    hist_over_random = []
    for i in range(len(xx)):
        hist_over_random.append(hist[i]/hist_r[i])
            
    plt.plot(xx, hist_over_random, 'o--')

def calculate_PL(list_of_list, domain):
    total_L = []
    total_L_r = []
    if domain == 'sci':
        for rec in list_of_list[:]:
            y = np.array([j[1] for j in rec])
            thr = np.median(y)
            L = calculate_period_length(y, thr)
            total_L += [L]
            
            new_y = random.sample(y, len(y))
            L = calculate_period_length(new_y, thr)
            total_L_r += [L]
    else:
        for rec in list_of_list[:]:
            y = np.array([j[0] for j in rec])
            thr = np.median(y)
            L = calculate_period_length(y, thr)
            total_L += [L]
            
            new_y = random.sample(y, len(y))
            L = calculate_period_length(new_y, thr)
            total_L_r += [L]
    fig = plt.figure(figsize = (6,6))
    ax = fig.add_axes([0.3, 0.3, 0.5, 0.5])
    bins = np.arange(0, 30, 2)
    hist, x = np.histogram(total_L, bins = bins, density = True)
    xx = (x[1:]+x[:-1])/2.0
    plt.plot(xx, hist, 'ro')
    
    bins = np.arange(0, 30, 2)
    hist, x = np.histogram(total_L_r, bins = bins, density = True)
    xx = (x[1:]+x[:-1])/2.0
    plt.plot(xx, hist, 'bo')
    plt.yscale('log')
    plt.xlim(0, 31)
    plt.ylim(10**-4, 1)

def generate_impact_sequence(lists_of_lists, v0, tau, stdd):
    simu_data = []
    for rec in lists_of_lists[:]:
        N = pd.Series(rec[:, 1]).value_counts().sort_index()
        std = stdd + np.random.uniform(-0.1, 0.1)
        low = v0 + np.random.uniform(-0.5, 0.5)
        high = v0 + 1.0 + np.random.uniform(-0.5, 0.5)
        L = tau
        start = random.sample(rec[:, 1], 1)[0]
        y = np.array(np.random.normal(mean_L, std, len(rec)))
        for i in range(len(rec)):
            if start<=rec[i][1]<start+L:
                y[i]=np.random.normal(mean_H, std)

        simu_data.append(np.array(zip(y, rec[:, 1])))
    return simu_data

def calculate_ma_start(LL, delta_N):
    """
    calculate c10_moving average(N)
    window size = N_ratio*N
    """
    #delta_N = int(round(len(LL)*N_ratio))
    #print delta_N
    ma = [np.mean(LL[i:i+delta_N]) for i in np.arange(0, len(LL)-delta_N, 1)]
    return np.array(ma)

def generate_data_ma(dic_data, field = 'sci'):
    """
    return dictionary of deltaN and ma
    """
    id2ma = {}
    for p in dic_data:
        rec = np.array(dic_data[p])
        years = rec[:, 1]
        if field == 'sci':
            data = np.log(rec[:, 0]+1.0)
        elif field == 'art':
            data = np.log(rec[:, 0]+1.0)
        else:
            data = rec[:, 0]
        
        delta_N = max(5, int(round(len(rec)*0.1)))
        #if delta_N <3:
        #    delta_N = 3
        x, ma = calculate_ma_start(data, delta_N)
        
        yy = [years[i] for i in x]
        count = pd.Series(yy).value_counts().sort_index()
        new_years = [i+j for i in count.index.values for j in \
                     np.arange(count.loc[i])*1.0/count.loc[i]]
        #print len(years, new_years)
        id2ma[p] = [delta_N, x, ma, years, new_years]
    return id2ma

def fit_hits_incre(p):
    """
    p: model parameters
    y: Gamma sequeence
    """
    # the start and end of each hot hand
    d1 = p[0]
    d2 = p[1]
    d3 = p[2]
    d4 = p[3]
    d5 = p[4]
    d6 = p[5]
    # the value of impact
    base = p[6]
    h1 = p[7]
    h2 = p[8]
    h3 = p[9]
    
    y_pred = [base for i in range(len(y))]
    for i in range(len(y)):
        if d1<=i<=d1+d2:
            y_pred[i] = base+h1
        if d1+d2+d3<=i<=d1+d2+d3+d4:
            y_pred[i] = base+h2
        if d1+d2+d3+d4+d5<=i<=d1+d2+d3+d4+d5+d6:
            y_pred[i] = base+h3
        
    return p, y_pred

def error_hits_regularization(p):
    """
    m_lambda: L1 penalty coefficient
    p: model parameters
    y: Gamma sequeence
    """
    params, y_pred = fit_hits(p)
    sum_square = np.sum((np.array(y) - np.array(y_pred))**2)
    return sum_square+m_lambda*len([i for i in p[:6] if 0<=i<=len(y)])

def generate_best_fit(dic_data_ma, dic_fit):
    """
    choose fit with largest r2
    """
    id2best_fit = {}
    for p in dic_fit:
        #print p
        delta_N, x, ma, years, new_years = dic_data_ma[p] 
        
        min_error = 10**5
        result = dic_fit[p]
        fit_best = result[0]
        for i in result:
            i = i/np.sum(i)*np.sum(ma)
            error = np.sum((ma - i)**2)
            if error<min_error:
                min_error = error
                fit_best = i

        id2best_fit[p] = [min_error, fit_best]
    return id2best_fit

def get_hot_hand_properties(dic_data, dic_best_fit, dic_data_m):
    """
    dic_data: real impact sequence
    dic_best_fit: fitting sequence
    dic_data_m: the moving average sequence
    return hot hand index and level of hot
    """
    id2hot = {}    
    id2num = {}
    for p in dic_best_fit:
        rec = dic_data[p]
        delta_N, x, ma, years, new_years = dic_data_m[p]
        threshold_h = np.std(ma) 
        threshold_L = 5
        fit_best = dic_best_fit[p]
        gamma = sorted(list(set(fit_best)))

        base_gamma = gamma[0]
        g_h = []
        for i in gamma[1:]:
            if i-base_gamma>threshold_h:
                g_h+=[i]   
        count = list(count_consequtive_items(fit_best))

        hit_index_list = []
        num_hit = 0
        hit_indexx = []
        for cc in range(len(count)):
            seq = count[cc]
            g = seq[0]
            L = seq[1]
            if g in g_h and L>threshold_L:
                #print g
                num_hit+=1
                if cc==0:
                    hit_index = np.arange(0, count[cc][1], 1)
                else:
                    hit_index = np.arange(np.sum([j[1] for j in count[:cc]]), np.sum([j[1] for j in count[:cc]])+count[cc][1], 1)
                year_index = [years[i] for i in hit_index]
                new_year_index = [new_years[i] for i in hit_index]
                hit_index_list.append([g, hit_index, year_index, new_year_index])
                hit_indexx+=list(hit_index)

            id2hot[p] = hit_index_list  
            id2num[p] = num_hit
    return id2hot, id2num


if __name__ == "__main__":
    
    path_data = 'scientists_c10.txt'
    sci_data  = load_data(path_data, 'sci')
    
    ### real_sequence ###
    order_1, order_2, order_3, _, _, _ = calculate_N_order(sci_data, 'sci')

    ### correlation ###
    calculate_phi(order_1, order_2)
    ### PL distribution ### 
    calculate_PL(sci_data, 'sci')
