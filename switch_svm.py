#!/usr/bin/python

'''
Created on 16 Nov 15

@author: Asher
'''
import numpy as np
import logging
import os
import random
from sklearn import svm, preprocessing, metrics
from sklearn.metrics import roc_curve, auc
from time import gmtime, strftime
import argparse


'''
Predict the load of a switch, vector contains the data of the ports of the switch
'''
def load_samples(input_file, features_per_switch):
    logging.info( "...Loading samples")
    samples = []
    loaded_cnt = 0
    switch_name_list = []
    # The first line doesn't have complete data yet, so we use it to take the switch names
    switch_clm_fill = True
    with open(input_file,'r') as f:
        for line in f:
            if line.startswith('#'):
                # ignoring comments
                continue
            raw_sample = line.split(',')
            loaded = int(raw_sample[0].strip())
            if loaded == 1 :
                loaded_cnt += 1
            sample = [loaded]
            for j in range(1, len(raw_sample)):
                logging.debug(raw_sample[j])
                if (j-1) % features_per_switch == 0:
                    if switch_clm_fill:
                        switch_name_list.append(raw_sample[j].strip() + " 0%d"%((j-1) % features_per_switch))
                    continue
                else:
                    sample.append(int(raw_sample[j].strip()))
            samples.append(sample)
            switch_clm_fill = False

    logging.debug("samples:" + str(samples))
    logging.debug("switches:" + str(switch_name_list))
    logging.info("Finished loading samples...")
    logging.info("Number of samples: %d"%len(samples))
    logging.info("Number of loaded switches: %d"%loaded_cnt)
    return samples

def classify_switch_data(sets, scale, write_each_class_results, label, classifier):
    logging.info("...Start Switch Load prediction.")

    result_all = []
    
    for j in range(len(sets)):
        logging.info( "...cross-folding, eval set: %d"%j)
        train_db,eval_db = prepare_training_set_for_cross_validation(sets, j)
    
        y_train = []
        x_all_train = []
        for fline in train_db:
            y_train.append(fline[0])
            x_all_train.append(fline[1:])
            
        y_eval = []
        x_all_eval = []
        for fline in eval_db:
            y_eval.append(fline[0])
            x_all_eval.append(fline[1:])

        if scale:
            x_all_eval, x_all_train = scale_data(x_all_eval, x_all_train)
        accuracy_alg, y_pred = classifier.classify(x_all_train, y_train, x_all_eval, y_eval)
        if write_each_class_results:
            result = post_process_per_class(accuracy_alg, y_eval, y_pred)
            result_all.append(result)
            out = ' '.join(map(str, result))
            logging.info('Set {2}: {0} {1}'.format(label, out, j))
        else:
            result = post_process(accuracy_alg, y_eval, y_pred)
            result_all.append(result)
            str_out = "accuracy {0}, precision {1}, recall {2}, F_measure {3}, roc_auc {4}, hamming_loss {5}"
            str_out = str_out.format(*result)
            logging.info('Set {1}: {0} \n'.format(str_out, j))

    logging.info(label)
    logging.info('Average result for cross validation')
    tmp = np.mean(np.array(result_all), axis=0)
    if not write_each_class_results:
        str_out = "accuracy {0}, precision {1}, recall {2}, F_measure {3}, roc_auc {4}, hamming_loss {5}".format(*tmp)
        logging.info('Average {0}'.format(str_out))
    else:
        str_out = "Average: F_measure_avg {0} accuracy {1} roc_auc {2} precision_Loaded {3}, recall_Loaded {4}," \
                  " F_measure_Loaded {5}, precision_Not_Loaded {6}, recall_Not_Loaded {7}, F_measure_Not_Loaded {8}," \
                  " BSR {9}".format(*tmp)
        logging.info(str_out)

    logging.info("End Switch Load prediction...")

#########################  End Switch Process   ########################################################

#########################  SVM Functions    ########################################################
def scale_data(x_eval, x_train):
    logging.info("...Start Scaling data.")
    # scaler = preprocessing.Scaler().fit(x_train)
    scaler = preprocessing.StandardScaler().fit(x_train)
    x_train = scaler.transform(x_train)
    x_eval = scaler.transform(x_eval)
    logging.info("End Scaling data...")
    return x_eval, x_train


def post_process( accuracy_alg, y_eval, y_pred):
    # Compute ROC curve and area the curve
    fpr, tpr, thresholds = roc_curve(y_eval, y_pred)
    roc_auc = auc(fpr, tpr)
    # Hamming loss: the percentage of the wrong labels to the total number of labels.
    # This is a loss function, so the optimal value is zero.
    # If normalize is True, return the fraction of misclassifications (float),
    # else it returns the number of misclassifications (int). The best performance is 0
    # zero_one_loss is the same as hamming_loss
    hamming_loss = metrics.zero_one_loss(y_eval, y_pred)
    # In multi-label classification, this function computes subset accuracy:
    # the set of labels predicted for a sample must exactly match the corresponding set of labels in y_true.
    accuracy = metrics.accuracy_score(y_eval, y_pred)
    # The F1 score can be interpreted as a weighted average of the precision and recall,
    # where an F1 score reaches its best value at 1 and worst score at 0
    # Macro-averaged performance scores are computed by first computing the scores for
    # the per-category contingency tables, and then averaging these per-category scores to compute the global means.
    # Micro-averaged performance scores are computed by first creating a global contingency table
    # whose cell values are the sums of the corresponding cells in the per-category contingency tables,
    # and then use this global contingency table to compute the micro-averaged performance scores
    # w,mi, ma same value for binary result
    F_measure_w = metrics.f1_score(y_eval, y_pred, average='weighted')
    # F_measure_mi = metrics.f1_score(y_eval, y_pred, average='micro')
    # F_measure_ma = metrics.f1_score(y_eval, y_pred, average='macro')
    # The precision is the ratio tp / (tp + fp) where tp is the number of true positives
    # and fp the number of false positives.
    # The precision is intuitively the ability of the classifier not to label as positive a sample that is negative.
    precision_w = metrics.precision_score(y_eval, y_pred, average='weighted')
    # precision_mi = metrics.precision_score(y_eval, y_pred, average='micro')
    # precision_ma = metrics.precision_score(y_eval, y_pred, average='macro')
    # The recall is the ratio tp / (tp + fn) where tp is the number of true positives
    # and fn the number of false negatives.
    # The recall is intuitively the ability of the classifier to find all the positive samples.
    recall_w = metrics.recall_score(y_eval, y_pred, average='weighted')
    # recall_mi = metrics.recall_score(y_eval, y_pred, average='micro')
    # recall_ma = metrics.recall_score(y_eval, y_pred, average='macro')
    logging.info("Results time {0} accuracy_alg {1} accuracy {2} ".format(strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                                                                          accuracy_alg, accuracy))
    logging.info(
        "precision {0}, recall {1}, F_measure {2}, hamming_loss {3}, roc_auc {4}".format(precision_w, recall_w,
                                                                                         F_measure_w, hamming_loss,
                                                                                         roc_auc))
    if abs(accuracy_alg - accuracy) > 0.001:
        logging.error("accuracy not the same")
    target_labels = ["Switch Not Loaded", "Switch Loaded"]
    logging.info(metrics.classification_report(y_eval, y_pred, labels=None, target_names=target_labels))
    logging.info("End Calculating SVM...")
    return [accuracy_alg, precision_w, recall_w, F_measure_w, roc_auc, hamming_loss]

def post_process_per_class(accuracy_alg, y_eval, y_pred):
    logging.debug("accuracy: " + str(accuracy_alg))
    logging.debug("y_eval: %s, y_pred: %s",y_eval,y_pred)
    logging.debug("y_eval-len: %d, y_pred-len: %d",len(y_eval),len(y_pred))
    num_1, num_0 = 0, 0
    evl_1, evl_0 = 0, 0
    accurate_1, accurate_0 = 0, 0
    for idx in range(len(y_eval)):
        yp, ye = y_pred[idx], y_eval[idx]
        if yp == 1:
            num_1 += 1
            if yp == ye:
                accurate_1 += 1
        else:
            num_0 += 1
            if yp == ye:
                accurate_0 += 1
        if ye == 1:
            evl_1 += 1
        else:
            evl_0 += 1
    precision_1 = 0
    if num_1 > 0:
        precision_1 = float(accurate_1) / num_1
    recall_1 = 0
    if evl_1 > 0:
        recall_1 = float(accurate_1) / evl_1
    F_measure_1 = 0
    if precision_1 + recall_1 > 0:
        F_measure_1 = 2 * (precision_1 * recall_1) / (precision_1 + recall_1)
    precision_0 = 0
    if num_0 > 0:
        precision_0 = float(accurate_0) / num_0
    recall_0 = 0
    if evl_0 > 0:
        recall_0 = float(accurate_0) / evl_0
    F_measure_0 = 0
    if precision_0 + recall_0 > 0:
        F_measure_0 = 2 * (precision_0 * recall_0) / (precision_0 + recall_0)
    BSR = (precision_1 + precision_0) / 2
    F_measure_avg = (F_measure_1 + F_measure_0) / 2
    accuracy = (float(accurate_0) + float(accurate_1)) / (num_0 + num_1)
    # Compute ROC curve and area the curve
    fpr, tpr, thresholds = roc_curve(y_eval, y_pred)
    roc_auc = auc(fpr, tpr)
    logging.info(
        "precision_1 {0}, recall_1 {1}, F_measure_1 {2}, precision_0 {3}, recall_0 {4}, F_measure_0 {5} BSR {6}".format(
            precision_1, recall_1, F_measure_1, precision_0, recall_0, F_measure_0, BSR))
    logging.info("num_1 {0}, accurate_1 {1}, evl_1 {2}, num_0 {3}, accurate_0 {4}, evl_0 {5}".format(
        num_1, accurate_1, evl_1, num_0, accurate_0, evl_0))
    if abs(accuracy_alg - accuracy) > 0.001:
        logging.error("accuracy not the same")
    logging.info("End Calculating SVM...")
    return [F_measure_avg, accuracy_alg, roc_auc, precision_1, recall_1, F_measure_1, precision_0, recall_0,
            F_measure_0, BSR, num_1, accurate_1, evl_1, num_0, accurate_0, evl_0]
#########################  Cross Validation ########################################################
"""
Prepare Cross-validation sets, num_folds is the number of sets, returns an array of sets
The set is built randomly
"""
def prepare_cross_validation_sets(samples, num_folds=5):
    logging.info("...Start Preparing Cross Validation Sets Data for SVM")

    set_size = int(len(samples)/num_folds)
    
    logging.debug("Computing %d cross Validation sets"%num_folds)
    
    fold_sets = {}
    for i in range(num_folds):
        fold_sets[i] = []
    
    random.shuffle(samples)
    for i in range(num_folds):
        for j in range(set_size):
            fold_sets[i].append(samples.pop())
    
    for i in range(num_folds):
        if len(samples) == 0:
            break
        fold_sets[i].append(samples.pop())
        
    for i in range(num_folds):
        logging.debug("...cross validation #%d: items %d"%(i, len(fold_sets[i])))

    logging.info("End Preparing Cross Validation Sets Data for SVM...")

    return fold_sets

"""
Prepare the training set and evaluation set for Cross-validation sets
"""
def prepare_training_set_for_cross_validation(sets, evalIdx):
    logging.info("...computing training set (eval set is %d)..."%evalIdx)
    
    train_db = []
    eval_db = list(sets[evalIdx])
    
    for i in range(len(sets)):
        if i != evalIdx:
            train_db.extend(list(sets[i]))
                
    logging.info("...done (training set: size %d , evaluation set: size %d )"%(len(train_db),len(eval_db)))
    
    return train_db, eval_db

#########################  End Cross Validation ########################################################

#########################  Start Run SVM Function     ########################################################


class Classifier(object):
    def classify(self,x_train, y_train, x_eval, y_eval):
        raise RuntimeError("Running abstract classifier!")

class SVMClassifier(Classifier):
    def __init__(self,p_C, p_Gamma, p_Kernel, p_class_weight):
        self.p_C = p_C
        self.p_Gamma = p_Gamma
        self.p_Kernel = p_Kernel
        self.p_class_weight = p_class_weight

    def classify(self, x_train, y_train, x_eval, y_eval):
        logging.info("...Start Calculating SVM.")

        if self.p_Kernel != 'linear':
            # SVC implements the "one-against-one" approach
            clf = svm.SVC(C=self.p_C, cache_size=500, class_weight=self.p_class_weight, coef0=0.0, degree=3,
                          gamma=self.p_Gamma, kernel=self.p_Kernel, probability=False, shrinking=True,
                          tol=0.001,verbose=False)
        else :
            # LinearSVC implements "one-vs-the-rest" multi-class strategy
            # class_weight - The 'auto' mode uses the values of y to automatically adjust weights inversely proportional
            # to class frequencies
            clf = svm.LinearSVC(C=self.p_C, class_weight=self.p_class_weight)

        clf.fit(x_train, y_train)
        y_pred = clf.predict(x_eval)
        accuracy_alg = clf.score(x_eval, y_eval)

        return accuracy_alg, y_pred

#########################  End Run SVM Function     ########################################################
#########################  End SVM Functions     ########################################################
def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input",required=True, help="The input file")
    # parser.add_argument("-o", "--output", default="Results_For_{0}.txt", help="The output file")
    parser.add_argument("-d", "--debug", action="store_true", help="Set verbosity to high (debug level)")
    # parser.add_argument("--write-class-results", action="store_true", help="Write class results to output")
    parser.add_argument("--write-each-class-results", action="store_true", help="Write each class results to output")
    # parser.add_argument("-q", "--dry-run", "--quiet", action="store_true", help="Dry run - no output")
    parser.add_argument("--features-per-switch", type=int, default=10, help="Amount of features per switch")
    parser.add_argument("--pC", type=float, default=1.0, help="p_C")
    parser.add_argument("--pGamma", type=float, default=0.0, help="p_Gamma")
    parser.add_argument("--pKernel", default='linear', help="p_Kernel")
    parser.add_argument("--p-class-weight", default=None, help="p class weight")
    parser.add_argument("--dont-scale", action="store_true", help="Don't scale data")
    args = parser.parse_args()
    return args


def create_label(args):
    label = "Classifier = {0} C={1} Gamma={2} Kernel {3} weight {4} "
    label = label.format("SVM", args.pC, args.pGamma, args.pKernel, args.p_class_weight)
    if args.dont_scale:
        label += "Data Not scaled "
    else:
        label += "Data scaled "

    return label


def main():
    args = parse_arguments()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    if not os.path.exists(args.input):
        logging.error("The input file \"%s\" was not found!"%args.input_file)
        return

    samples = load_samples(args.input, args.features_per_switch)

    sets = prepare_cross_validation_sets(samples)

    label = create_label(args)

    classifier = SVMClassifier(args.pC, args.pGamma, args.pKernel, args.p_class_weight)

    classify_switch_data(sets,not args.dont_scale,args.write_each_class_results, label, classifier)


if __name__ == '__main__':
    main()
