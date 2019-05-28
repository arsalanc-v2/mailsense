#!/usr/bin/env python3

import argparse
import pandas as pd
from fastai import *
from fastai.text import *

def load_data(path):
	df = pd.read_csv(path)
	train_df = df[df[DATASET_COMPONENT_LABEL] == 'train']
	val_df = df[df[DATASET_COMPONENT_LABEL] == 'val']
	test_df = df[df[DATASET_COMPONENT_LABEL] == 'test']

	# Language model data
	data_lm = TextLMDataBunch.from_df(train_df=train_df, valid_df=val_df, test_df=test_df, text_cols=args.textcolumn, label_cols=args.labelcolumn, path="")
	# Classifier model data
	data_clas = TextClasDataBunch.from_df(train_df=train_df, valid_df=val_df, test_df=test_df, vocab=data_lm.train_ds.vocab, bs=32, text_cols=args.textcolumn, label_cols=args.labelcolumn, path="")
	return data_lm, data_clas

def train(data_lm, data_clas, lm_epochs=1, tc_epochs=1):
	# create language model with pretrained weights
	learn = language_model_learner(data_lm, arch=AWD_LSTM, drop_mult=0.5)
	# train language model using one cycle policy
	learn.fit_one_cycle(lm_epochs, 1e-2)
	learn.save_encoder(LANGUAGE_MODEL_NAME)
	learn = text_classifier_learner(data_clas, arch=AWD_LSTM, drop_mult=0.5)
	learn.load_encoder(LANGUAGE_MODEL_NAME)
	learn.fit_one_cycle(tc_epochs, 1e-2)
	return learn

def show_results(learn):
	preds, y, losses = learn.get_preds(DatasetType.Train, with_loss=True)
	interp = ClassificationInterpretation(learn, preds, y, losses)
	print(interp.confusion_matrix(slice_size=10))
	print(learn.show_results())

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-dp', '--datasetpath', help='str: path to csv dataset', type=str, action='store', required=True)
	parser.add_argument('-tcol', '--textcolumn', help='int: column index of text', type=int, action='store', required=True)
	parser.add_argument('-lcol', '--labelcolumn', help='int: column index of labels', type=int, action='store', required=True)
	parser.add_argument('-lme', '--languagemodelepochs', help='int: number of epochs to train the language model learner', type=int, action='store', default=1)
	parser.add_argument('-tce', '--textclassifierepochs', help='int: number of epochs to train the text classifier', type=int, action='store', default=1)
	args = parser.parse_args()

	DATASET_COMPONENT_LABEL = 'set'
	LANGUAGE_MODEL_NAME = 'languagemodel_encoder'
	TEXT_MODEL_NAME = 'textclassifier.pkl'

	data_lm, data_clas = load_data(args.datasetpath)
	learn = train(data_lm, data_clas, args.languagemodelepochs, args.textclassifierepochs)
	learn.export('models/' + TEXT_MODEL_NAME)
	show_results(learn)