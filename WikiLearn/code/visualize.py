from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

def plot_vectors(vecs, titles):
    print("Plotting...")

    vecs = TSNE(n_components=2, early_exaggeration=4.0).fit_transform(vecs)
    fig = plt.figure()
    for i in xrange(len(titles)):
        plt.annotate(titles[i].replace('_','\n'), xy=(vecs[i,0],vecs[i,1]), fontsize='1', fontname='Arial', ha='center', va='center')
    plt.axis((np.min(vecs[:,0]),np.max(vecs[:,0]),np.min(vecs[:,1]),np.max(vecs[:,1])))
    plt.axis('off')
    plt.savefig('categories.png', dpi=800, bbox_inches='tight', transparent="True", pad_inches=0)