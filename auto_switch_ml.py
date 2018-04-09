#!/usr/bin/python

'''
Created on 16 Nov 15

@author: Asher, YossiS
'''
import numpy as np
import logging
import os
import random
from sklearn.cross_validation import train_test_split
from sklearn.metrics import f1_score, accuracy_score, classification_report
from time import gmtime, strftime
import argparse
from autosklearn.classification import AutoSklearnClassifier


'''
Predict the load of a switch, vector contains the data of the ports of the switch
'''
def load_samples(input_file, features_per_switch):
    logging.info( "...Loading samples")
    samples = []
    loaded_list = []
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
            loaded_list.append(loaded)
            sample = []
            for j in range(1, len(raw_sample)):
                if (j-1) % features_per_switch == 0:
                    if switch_clm_fill:
                        switch_name_list.append(raw_sample[j].strip() + " 0%d"%((j-1) % features_per_switch))
                else:
                    sample.append(int(raw_sample[j].strip()))
            samples.append(sample)
            switch_clm_fill = False

    #logging.debug("samples:" + str(samples))
    logging.debug("switches:" + str(switch_name_list))
    logging.info("Finished loading samples...")
    logging.info("Number of samples: %d"%len(samples))
    logging.info("Number of loaded switches: %d"%sum(loaded_list))
    return samples, loaded_list

def classify_switch_data(samples, loaded_list, classifier):
    logging.info("...Start Switch Load prediction.")

    X_train, X_test, y_train, y_test = \
        train_test_split(np.array(samples), np.array(loaded_list), random_state=42)

    y_pred = classifier.classify(X_train, y_train, X_test)

    logging.getLogger().addHandler(logging.StreamHandler())

    logging.info("Models Selected:\n" + classifier.show_models())

    post_process(y_test, y_pred)

    logging.info("End Switch Load prediction...")


def post_process(y_true, y_pred):
    logging.debug("y_true: %s, y_pred: %s",y_true,y_pred)
    logging.debug("y_true-len: %d, y_pred-len: %d",len(y_true),len(y_pred))

    result = []
    result.append(f1_score(y_true, y_pred))
    result.append(accuracy_score(y_true, y_pred))

    #str_out = "F_measure_avg {0} accuracy {1} roc_auc {2} precision_Loaded {3}, recall_Loaded {4}," \
    #          " F_measure_Loaded {5}, precision_Not_Loaded {6}, recall_Not_Loaded {7}, F_measure_Not_Loaded {8}," \
    #          " BSR {9}".format(*tmp)
    str_out = "F_measure_avg {0} accuracy {1}".format(*result)
    logging.info('Results (training with cross validation):\n' + str_out)
    logging.info(classification_report(y_true, y_pred,target_names=["unloaded","loaded"]))


class Classifier(object):
    def classify(self, X_train, y_train, X_test):
        raise RuntimeError("Running abstract classifier!")

class AutoClassifier(Classifier):
    def __init__(self, time_left_for_this_task, per_run_time_limit, folds):
        now = strftime("%Y-%m-%d-%H-%M-%S", gmtime())
        self.automl = AutoSklearnClassifier(
            time_left_for_this_task=time_left_for_this_task,
            per_run_time_limit=per_run_time_limit,
            #tmp_folder='/tmp/autosklearn_switch_tmp',
            #output_folder='/tmp/autosklearn_switch_out',
            #delete_tmp_folder_after_terminate=False,
            #delete_output_folder_after_terminate=False,
            #shared_mode=True,
            resampling_strategy='cv',
            resampling_strategy_arguments={'folds': folds})

    def classify(self, X_train, y_train, X_test):
        # fit() changes the data in place, but refit needs the original data. We
        # therefore copy the data. In practice, one should reload the data
        self.automl.fit(X_train.copy(), y_train.copy())
        # During fit(), models are fit on individual cross-validation folds. To use
        # all available data, we call refit() which trains all models in the
        # final ensemble on the whole dataset.
        self.automl.refit(X_train.copy(), y_train.copy())

        predictions = self.automl.predict(X_test)

        return predictions


    def show_models(self):
        return self.automl.show_models()


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input",required=True, help="The input file")
    parser.add_argument("-d", "--debug", action="store_true", help="Set verbosity to high (debug level)")
    parser.add_argument("--features-per-switch", type=int, default=10, help="Amount of features per switch")
    parser.add_argument("--time-left-for-this-task", type=int, default=120, help="Time limit in seconds for the search of appropriate models")
    parser.add_argument("--per-run-time-limit", type=int, default=30, help="Time limit for a single call to the machine learning model")
    parser.add_argument("--folds", type=int, default=5, help="Amount of cross-validation folds")
    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    if not os.path.exists(args.input):
        logging.error("The input file \"%s\" was not found!"%args.input)
        return -1

    samples, loaded_list = load_samples(args.input, args.features_per_switch)

    classifier = AutoClassifier(args.time_left_for_this_task,
                                args.per_run_time_limit,
                                args.folds)

    classify_switch_data(samples, loaded_list, classifier)

    logging.info("all done!")

if __name__ == '__main__':
    main()
