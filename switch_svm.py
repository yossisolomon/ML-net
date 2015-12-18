'''
Created on 16 Nov 15

@author: Asher
'''
import numpy as np
import logging
import logging.config
import csv
import os
import os.path
import time
import math
import nltk
import random
import sklearn
from sklearn import svm, preprocessing, metrics
from sklearn.metrics import roc_curve, auc
from time import gmtime, strftime
from optparse import OptionParser
#from utils import *

#########################  Switch Process   ########################################################
#Switch_inputFile = 'sflowCSV-2015-11-17T14_17_26.csv'
#Switch_inputFile = 'sflowCSV-2015-11-20T02-51-31.csv'
#Switch_inputFile = 'sflowCSV-2015-12-05T04-09-41-499978.dat'
Switch_inputFile = 'not exixts'

#Switch_output_file = "Switch_Load_Results.txt"
Switch_output_file = "Results_For_{0}.txt"
Write_Class_Results = False
Each_Class_Results = True
quiet = False

p_C = 1.0
p_Gamma = 0.0
p_Kernel = 'linear' #'rbf'
p_class_weight = None #'auto'
scale = True

'''
Predict the load of a switch, vector contains the data of the ports of the switch
'''
def classify_switch_data():
    print( "...Start Switch Load prediction.")
    
    global Switch_inputFile
    if options.input != None:
        Switch_inputFile = options.input
    
    if not os.path.exists(Switch_inputFile):
        print( "The input file name was not found. Please use command: python Yosi_switch_svm.py --i=input file name.txt")
        print("End Switch Load prediction...")
        return
    
    print( "...Start Preparing Data for SVM.")
    f = open(Switch_inputFile,'r')
    global Write_Class_Results
    global Each_Class_Results
    global quiet 
    f_out = None
    if not quiet : 
        if Write_Class_Results :
            if not Each_Class_Results:
                f_out = open(Switch_output_file.format("Best_" + Switch_inputFile.replace(".csv", "")), 'a')
            else:
                f_out = open(Switch_output_file.format("Each_Class_Best_" + Switch_inputFile.replace(".csv", "")), 'a')
        else:
            if Each_Class_Results:
                f_out = open(Switch_output_file.format(Switch_inputFile.replace(".csv", "")), 'a')
            else:
                f_out = open(Switch_output_file.format("Each_Class_" + Switch_inputFile.replace(".csv", "")), 'a')
        #f_out.write("Results for file {0} ".format(Switch_inputFile))
        f_out.write('\n')
        f_out.flush()
        
    lines = []
    idx = 0
    loaded_cnt = 0
    switch_clm_target = ["Switch Not Loaded", "Switch Loaded"]
    switch_clm_list = []
    switch_clm_fill = True
    for fline in f:
        if fline.startswith('#') :
            continue
        idx+=1
        line = fline.split(',')
        loaded = int(line[0].strip())
        if loaded == 1 :
            loaded_cnt+=1 
        #if idx == 1000 :
        #    break
        svm_line = []
        svm_line.append(loaded)
        last_clm_name = ""
        for j in range(1, len(line)):
            #print (line[j])
            if(((j-1) % 10) == 0 ):
                last_clm_name = line[j].strip() + " 0{0}"
                #print (line[j])
                continue
            else :
                if switch_clm_fill:
                    switch_clm_list.append(last_clm_name.format(((j-1) % 10)))
                val = int(line[j].strip())
                svm_line.append(val)
        lines.append(svm_line)
        switch_clm_fill = False
    
    #print (lines)
    #print (switch_clm_list)    
    f.close()
    if not quiet:
        f_out.write("Number of samples {0} \n".format(idx))
        f_out.write("Number of loaded switches {0} \n".format(loaded_cnt))
    print("Number of samples {0} ".format(idx))
    print("Number of loaded switches {0} ".format(loaded_cnt))
    print( "End Preparing Data for SVM...")
    
    print( "...Start Preparing Cross Validation Sets Data for SVM")
    sets = prepareCrossValidationSets( lines )
    print( "End Preparing Cross Validation Sets Data for SVM...")
    
    print("... Start SVM Run")
    global p_C
    global p_Gamma    
    global p_Kernel
    global p_class_weight
    info = "Switch load classifier"
    #label = "info = {5} classifier = {0} C={1} Gamma={2} Kernel {3} weight {4} ".format("SVM", p_C, p_Gamma, p_Kernel, p_class_weight, info)
    label = "Classifier = {0} C={1} Gamma={2} Kernel {3} weight {4} ".format("SVM", p_C, p_Gamma, p_Kernel, p_class_weight)
    if scale :
        label += "Data scaled "
    else :
        label += "Data Not scaled "
    if not quiet:
        f_out.write(label + '\n')
        f_out.flush()
    result_all = []
    
    for j in range(len(sets)):
        print( "...cross-folding, eval set: %d"%j)
        trainDB,evalDB = prepareTrainSet4CrossValidSets(sets, j)
    
        y_train = []
        x_all_train = []
        for fline in trainDB:
            y_train.append(fline[0])
            x_all_train.append(fline[1:])
            
        y_eval = []
        x_all_eval = []
        for fline in evalDB:
            y_eval.append(fline[0])
            x_all_eval.append(fline[1:])
            
        result = runSVM(x_all_train, y_train, x_all_eval, y_eval, scale, switch_clm_list, switch_clm_target, Write_Class_Results, f_out)
        result_all.append(result)
        if not quiet :
            write_out_set_result(result, label, f_out, j)
            
    if not quiet :    
        f_out.write('Average result for cross validation \n')
        f_out.flush()
        write_out(result_all, label, f_out)
        f_out.close()

    print("End SVM Run ...")
    
    print("End Switch Load prediction...")
    
#########################  End Switch Process   ########################################################

#########################  SVM Functions    ########################################################
#########################  Cross Validation ########################################################
"""
Prepare Cross-validation sets, the input num_folds is the number of sets, returns an array of sets
The set is build randomly 
"""
def prepareCrossValidationSets(population, num_folds = 5):
    
    pop = population
    setSize = (int)(len(pop)/num_folds)
    setNum = (int)(len(pop) / setSize)
    
    #print( "Computing %d cross Validation sets"%setNum ) 
    
    foldSets = {}
    for i in range(setNum):
        foldSets[i] = []
    
    random.shuffle( pop )    
    for i in range(setNum):
        for j in range(setSize):
            foldSets[i].append(pop.pop())
    
    for i in range(setNum):
        if len(pop) == 0 :
            break
        foldSets[i].append(pop.pop())
        
    #for i in range(setNum):
    #    print( "...cross validation #%d: items %d"%(i, len(foldSets[i]) ))

    return foldSets

"""
Prepare the training set and evaluation set for Cross-validation sets
"""
def prepareTrainSet4CrossValidSets (popSets, evalIdx) :
    print( "...computing training set (eval set is %d)..."%evalIdx )
    
    trainDB = []
    evalDB = list(popSets[evalIdx])
    
    for i in range(len(popSets)):
        if i!=evalIdx: 
            trainDB.extend(list(popSets[i])) 
                
    print( "...done (training set: size %d , evaluation set: size %d )"%(len(trainDB),len(evalDB) ))
    
    return trainDB, evalDB

#########################  End Cross Validation ########################################################

#########################  Start Run SVM Function     ########################################################
def runSVM(x_train, y_train, x_eval, y_eval, scale, labels, target_labels, Write_Class_Results, f_out):
    print( "...Start Calculating SVM.")
    if scale :
        print( "...Start Scaling data.")
        #scaler = preprocessing.Scaler().fit(x_train)
        scaler = preprocessing.StandardScaler().fit(x_train)
        #print x_train[0]
        x_train = scaler.transform(x_train)
        #print x_train[0]
        x_eval = scaler.transform(x_eval)
        print( "End Scaling data...")
    
    global p_C
    global p_Gamma    
    global p_Kernel
    global p_class_weight
    
    if p_Kernel != 'linear':
        #SVC implement the "one-against-one" approach
        clf = svm.SVC(C=p_C, cache_size=500, class_weight=p_class_weight, coef0=0.0, degree=3,gamma=p_Gamma, kernel=p_Kernel, probability=False, shrinking=True, tol=0.001,verbose=False)
    else :
        # LinearSVC implements "one-vs-the-rest" multi-class strategy
        # class_weight - The 'auto' mode uses the values of y to automatically adjust weights inversely proportional to class frequencies
        #clf = svm.LinearSVC(C=p_C, class_weight=p_class_weight, dual=True, fit_intercept=True,intercept_scaling=1, loss='l2', multi_class='ovr', penalty='l2',random_state=None, tol=0.0001, verbose=0)
        clf = svm.LinearSVC(C=p_C, class_weight=p_class_weight)
    
    clf.fit(x_train, y_train)
    y_pred = clf.predict(x_eval)
    accuracy_alg = clf.score(x_eval, y_eval)
    
    #'''        
    #print("#############################  My Result Calculation ####################################################")
    
    num_1, num_0 = 0, 0
    evl_1, evl_0 = 0, 0
    accurate_1, accurate_0 = 0, 0
    for idx in range(len(y_eval)) :
        yp, ye = y_pred[idx], y_eval[idx]  
        if yp == 1 :
            num_1 += 1
            if yp == ye:
                accurate_1+=1
        else :
            num_0 += 1
            if yp == ye:
                accurate_0+=1
        if ye == 1 :
            evl_1 += 1
        else :
            evl_0 += 1
    
    precision_1 = 0
    if num_1 > 0 :    
        precision_1 = float(accurate_1) / num_1
    recall_1 = 0
    if evl_1 > 0 :
        recall_1 = float(accurate_1) / evl_1
    F_measure_1 = 0
    if precision_1 + recall_1 > 0 :
        F_measure_1 = 2 * (precision_1 * recall_1) / (precision_1 + recall_1)
    
    precision_0 = 0
    if num_0 > 0 :
        precision_0 = float(accurate_0) / num_0
    recall_0 = 0
    if evl_0 > 0 :
        recall_0 = float(accurate_0) / evl_0
    F_measure_0 = 0
    if precision_0 + recall_0 > 0 : 
        F_measure_0 = 2 * (precision_0 * recall_0) / (precision_0 + recall_0)
    
    BSR = (precision_1 + precision_0) / 2 
    F_measure_avg = (F_measure_1 + F_measure_0) / 2
    accuracy = (float(accurate_0) + float(accurate_1)) / (num_0 + num_1)
    
    # Compute ROC curve and area the curve
    fpr, tpr, thresholds = roc_curve(y_eval, y_pred)
    roc_auc = auc(fpr, tpr)
    
    print ("precision_1 {0}, recall_1 {1}, F_measure_1 {2}, precision_0 {3}, recall_0 {4}, F_measure_0 {5} BSR {6}".format(precision_1, recall_1, F_measure_1, precision_0, recall_0, F_measure_0, BSR))
    print ("num_1 {0}, accurate_1 {1}, evl_1 {2}, num_0 {3}, accurate_0 {4}, evl_0 {5}".format(num_1, accurate_1, evl_1, num_0, accurate_0, evl_0))
    if abs(accuracy_alg - accuracy) > 0.001:
        print ("accuracy not the same")
        
    global Each_Class_Results
    if Each_Class_Results:
        return [F_measure_avg, accuracy_alg, roc_auc, precision_1, recall_1, F_measure_1, precision_0, recall_0, F_measure_0, BSR, num_1, accurate_1, evl_1, num_0, accurate_0, evl_0]
    #'''
        
    #print("#############################  System Result Calculation ####################################################")
    # Compute ROC curve and area the curve
    fpr, tpr, thresholds = roc_curve(y_eval, y_pred)
    roc_auc = auc(fpr, tpr)
               
    #Hamming loss: the percentage of the wrong labels to the total number of labels. This is a loss function, so the optimal value is zero.
    #hl = metrics.hamming_loss(y_eval, y_pred)
    #If normalize is True, return the fraction of misclassifications (float), else it returns the number of misclassifications (int). The best performance is 0
    # zero_one_loss is the same as hamming_loss
    hamming_loss = metrics.zero_one_loss(y_eval, y_pred)
    #In multilabel classification, this function computes subset accuracy: the set of labels predicted for a sample must exactly match the corresponding set of labels in y_true.
    accuracy = metrics.accuracy_score(y_eval, y_pred)
    #accuracy = metrics.accuracy_score(y_eval, y_pred, normalize=True)
    # The F1 score can be interpreted as a weighted average of the precision and recall, where an F1 score reaches its best value at 1 and worst score at 0
    
    #Macro-averaged performance scores are computed by first computing the scores for the per-category contingency tables and then
    #averaging these per-category scores to compute the global means. 
    #Micro-averaged performance scores are computed by first creating a global contingency table whose cell values are the sums of the 
    #corresponding cells in the per-category contingency tables, and then use this global contingency table to compute the micro-averaged performance scores
    
    #w,mi, ma same value for binary result 
    F_measure_w = metrics.f1_score(y_eval, y_pred, average='weighted') 
    #F_measure_mi = metrics.f1_score(y_eval, y_pred, average='micro')
    #F_measure_ma = metrics.f1_score(y_eval, y_pred, average='macro')
    #The precision is the ratio tp / (tp + fp) where tp is the number of true positives and fp the number of false positives. The precision is intuitively the ability of the classifier not to label as positive a sample that is negative.
    precision_w = metrics.precision_score(y_eval, y_pred, average='weighted')
    #
    precision_mi = metrics.precision_score(y_eval, y_pred, average='micro')
    #precision_ma = metrics.precision_score(y_eval, y_pred, average='macro')
    #The recall is the ratio tp / (tp + fn) where tp is the number of true positives and fn the number of false negatives. The recall is intuitively the ability of the classifier to find all the positive samples.
    recall_w = metrics.recall_score(y_eval, y_pred, average='weighted')
    #recall_mi = metrics.recall_score(y_eval, y_pred, average='micro')
    #recall_ma = metrics.recall_score(y_eval, y_pred, average='macro')
      
    print ("Results time {0} accuracy_alg {1} accuracy {2} ".format(strftime("%Y-%m-%d %H:%M:%S", gmtime()), accuracy_alg, accuracy)) 
    print ("precision {0}, recall {1}, F_measure {2}, hamming_loss {3}, roc_auc {4}".format(precision_w, recall_w, F_measure_w, hamming_loss, roc_auc))
    if abs(accuracy_alg - accuracy) > 0.001:
        print ("accuracy not the same")
    print (metrics.classification_report(y_eval, y_pred, labels=None, target_names=target_labels))  
    if Write_Class_Results:
        f_out.write(metrics.classification_report(y_eval, y_pred, labels=None, target_names=target_labels))
        f_out.flush()  
    return [accuracy_alg, precision_w, recall_w, F_measure_w, roc_auc, hamming_loss]

    print( "End Calculating SVM...")
    
#########################  End Run SVM Function     ########################################################

def write_out_set_result(x, label, f_out, j):
    out = ' '.join(map(str, x))
    global Each_Class_Results
    if not Each_Class_Results:
        #[accuracy_alg, precision_w, recall_w, F_measure_w, roc_auc, hamming_loss]
        str_out = ("accuracy {0}, precision {1}, recall {2}, F_measure {3}, roc_auc {4}, hamming_loss {5}".format(*x))
        f_out.write('Set {1}: {0} \n'.format(str_out, j))
    else:
        #[F_measure_avg, accuracy_alg, roc_auc, precision_1, recall_1, F_measure_1, precision_0, recall_0, F_measure_0, BSR, num_1, accurate_1, evl_1, num_0, accurate_0, evl_0]
        f_out.write('Set {2}: {0} {1} \n'.format(label, out, j))
    f_out.flush()

def write_out(x, label, f_out):
    tmp = np.mean(np.array(x), axis=0)
    out = ' '.join(map(str, tmp))
    global Each_Class_Results
    if not Each_Class_Results:
        #[accuracy_alg, precision_w, recall_w, F_measure_w, roc_auc, hamming_loss]
        str_out = ("accuracy {0}, precision {1}, recall {2}, F_measure {3}, roc_auc {4}, hamming_loss {5}".format(*tmp))
        f_out.write('Average {0} \n'.format(str_out))
    else:
        #[F_measure_avg, accuracy_alg, roc_auc, precision_1, recall_1, F_measure_1, precision_0, recall_0, F_measure_0, BSR, num_1, accurate_1, evl_1, num_0, accurate_0, evl_0]
        str_out = ("Average: F_measure_avg {0} accuracy {1} roc_auc {2} precision_Loaded {3}, recall_Loaded {4}, F_measure_Loaded {5}, precision_Not_Loaded {6}, recall_Not_Loaded {7}, F_measure_Not_Loaded {8} BSR {9}".format(*tmp))
        print (str_out)
        f_out.write(str_out)
        #f_out.write('{0} {1} \n'.format(label, out))
    f_out.flush()
    
#########################  End SVM Functions     ########################################################
'''        
Main Procedure
''' 
def main(args = None):
    global options
    usage = "usage: %prog [options] arg"
    parser = OptionParser(usage)     
    parser.add_option("-i", "--input", default=None, help="The input file")
    #parser.add_option( "--debug", default=False, action="store_true", help="Set verbosity to high (debug level)")
        
    #if options.no_cmd:
    if args != None :
        (options, args) = parser.parse_args(args)
    else:
        (options, args) = parser.parse_args()

    #if options.debug:
    #    logger.setLevel(logging.DEBUG)
    #else:
    #    logger.setLevel(logging.INFO)
     
    classify_switch_data()
        
if __name__ == '__main__':
    main()
    
    