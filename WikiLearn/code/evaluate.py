import numpy as np
import itertools
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
from sklearn.metrics import hamming_loss

def evaluate(y_test, y_pred, classes):
    for i,c in enumerate(classes):
        score = 1.0-hamming_loss(y_test[:,i], y_pred[:,i], classes)
        print("Accuracy for predicting '%s': %0.1f%%" % (c, 100.0*score))
    return 

def plot_confusion_matrix(y_test, y_pred, classes, normalize=False):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """

    title='Confusion matrix'
    cmap=plt.cm.Blues

    # Compute confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    
    # Plot normalized confusion matrix
    plt.figure()

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j,i,cm[i, j],horizontalalignment="center",color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.show()