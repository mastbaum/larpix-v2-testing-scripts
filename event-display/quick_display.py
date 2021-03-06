import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import h5py
import argparse
import matplotlib
import sys
plt.ion()

def vol3d(x,y,z,q,*geom,name=None,fig=None,points=False):
    xyz = np.array(list(zip(x,y,z)))
    q = q+1e-9
    if not points:
        vox_q, edges = np.histogramdd(xyz, weights=q,
            bins=(
                np.linspace(geom[0],geom[1],
                    int((geom[1]-geom[0])/geom[-2])+1),
                np.linspace(geom[2],geom[3],
                    int((geom[3]-geom[2])/geom[-2])+1),
                np.linspace(geom[4],geom[5],
                    int((geom[5]-geom[4])/geom[-1])+1),
            ))
    norm = lambda x: np.clip((x - max(np.min(x),0.001)) / (np.max(x) - max(np.min(x),0.001)),0,1)
    cmap = plt.cm.get_cmap('plasma')
    if not points:
        vox_color = cmap(norm(vox_q))
        vox_color[..., 3] = norm(vox_q)
    else:
        vox_color = cmap(norm(q))
        vox_color[..., 3] = norm(q)

    ax = fig.add_subplot(1,2,2, projection='3d')
    if not points:
        ax.voxels(*np.meshgrid(*edges, indexing='ij'), vox_q, facecolors=vox_color)
    else:
        ax.scatter(xyz[:,0],xyz[:,1],xyz[:,2],c=vox_color,alpha=0.5)
    ax.set_xlabel('x [mm]')
    ax.set_ylabel('y [mm]')
    ax.set_zlabel('t [0.1us]')
    plt.xlim(geom[0],geom[1])
    plt.ylim(geom[2],geom[3])
    plt.tight_layout()

    plt.draw()
    return fig

def line3d(x,y,z,*geom,name=None,fig=None,points=False):
    xyz = np.array(list(zip(x,y,z)))

    # ax = fig.add_subplot('122', projection='3d')
    ax = fig.gca()
    if not points:
        ax.plot(x,y,z,alpha=1)
    else:
        ax.scatter(xyz[:,0],xyz[:,1],xyz[:,2],s=1,alpha=0.75)
    ax.set_xlabel('x [mm]')
    ax.set_ylabel('y [mm]')
    ax.set_zlabel('t [0.1us]')
    plt.xlim(geom[0],geom[1])
    plt.ylim(geom[2],geom[3])
    plt.tight_layout()

    plt.draw()
    return fig

def line2d(x,y,*geom,name=None,fig=None):
    xy = np.array(list(zip(x,y)))

    ax = fig.gca()
    ax.plot(x,y)
    plt.tight_layout()

    plt.draw()
    return fig

def proj2d(x,y,q,*geom,name=None,fig=None):
    ax = fig.add_subplot(2,2,1)
    q = q+1e-9
    h = ax.hist2d(x,y,bins=(
        np.linspace(geom[0],geom[1],int((geom[1]-geom[0])/geom[-2])+1),
        np.linspace(geom[2],geom[3],int((geom[1]-geom[0])/geom[-2])+1)
        ),
        weights=q,
        cmin=0.0001,
        cmap='plasma'
    )
    plt.xlabel('x [mm]')
    plt.ylabel('y [mm]')
    plt.tight_layout()

    plt.draw()
    plt.colorbar(h[3],label='charge [ke]')
    return fig

def proj_time(t,q,*geom,name=None,fig=None):
    ax = fig.add_subplot(2,2,3)
    q = q+1e-9
    ax.hist(t, weights=q,
        bins=np.linspace(geom[4],geom[5],
                int((geom[5]-geom[4])/geom[-1])+1),
        histtype='step', label='binned')
    plt.xlabel('timestamp [0.1us]')
    plt.ylabel('charge [ke]')
    plt.tight_layout()

    plt.draw()
    return fig

def hit_times(t,q,*geom,name=None,fig=None):
    ax = fig.add_subplot(2,2,3)
    q = q+1e-9
    t,q = zip(*sorted(zip(t[t<geom[5]],q[t<geom[5]])))
    ax.plot(t,q,'r.', label='hits')
    plt.xlabel('timestamp [0.1us]')
    plt.ylabel('charge [ke]')
    plt.legend()
    plt.tight_layout()

    plt.draw()
    return fig

def generate_plots(event, f, geom=[], fig=None):
    name = 'Event {}/{} ({})'.format(event['evid'],len(f['events']),f.filename)

    hits = f['hits']
    tracks = f['tracks'] if 'tracks' in f.keys() else None

    hit_ref = event['hit_ref']
    track_ref = event['track_ref'] if tracks else None

    x = hits[hit_ref]['px']
    y = hits[hit_ref]['py']
    z = hits[hit_ref]['ts'] - event['ts_start']
    q = hits[hit_ref]['q'] * 0.250

    if tracks and event['ntracks']:
        track_start = tracks[track_ref]['start'][:,[0,1,3]]
        track_end = tracks[track_ref]['end'][:,[0,1,3]]

    if not fig:
        fig = plt.figure(name)
    fig = vol3d(x,y,z,q,*geom,name=name,fig=fig)
    if tracks and event['ntracks']:
        for s,e in zip(track_start,track_end):
            fig = line3d((s[0],e[0]),(s[1],e[1]),(s[2],e[2]),*geom,name=name,fig=fig)
        for track in tracks[track_ref]:
            hit_ref = track['hit_ref']
            fig = line3d(hits[hit_ref]['px'],hits[hit_ref]['py'],hits[hit_ref]['ts']-event['ts_start'],*geom,name=name,fig=fig,points=True)
    fig = proj2d(x,y,q,*geom,name=name,fig=fig)
    if tracks and event['ntracks']:
        for s,e in zip(track_start,track_end):
            fig = line2d((s[0],e[0]),(s[1],e[1]),*geom,name=name,fig=fig)
    fig = proj_time(z,q,*geom,name=name,fig=fig)
    fig = hit_times(z,q,*geom,name=name,fig=fig)
    fig.canvas.set_window_title(name)
    return fig

def open_file(filename):
    return h5py.File(filename,'r')

def main(args):
    f = open_file(args.input)
    events = f['events']
    tracks = f['tracks'] if 'tracks' in f.keys() else None
    hits = f['hits']
    fig = None
    ev = 0
    while True:
        print('displaying event {} with nhit_sel={}'.format(ev,args.nhit_sel))
        if ev >= np.sum(events['nhit'] > args.nhit_sel):
            sys.exit()
        event = events[events['nhit'] > args.nhit_sel][ev]
        print('Event:',event)
        if tracks and event['ntracks']: print('Track:',tracks[event['track_ref']])
        print('Hits:',hits[event['hit_ref']])
        fig = generate_plots(event, f, args.geom_limits, fig=fig)
        user_input = input('Next event (q to exit/enter for next/number to skip to position)?\n')
        print(user_input)
        if not len(user_input) or user_input[0] == '':
            ev += 1
        elif user_input[0].lower() == 'q':
            sys.exit()
        else:
            ev = int(user_input)
        plt.clf()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--input',required=True,help='''
    Input event display file
    ''')
    parser.add_argument('--nhit_sel',default=0, type=int, help='''
    Optional, sub-select on nhit greater than this value
    ''')
    parser.add_argument('--geom_limits', default=[-159.624,159.624,-159.624,159.624,0,1900,4.434,23], nargs=8, type=float, metavar=('XMIN','XMAX','YMIN','YMAX','TMIN','TMAX','PIXEL_PITCH','TIME_VOXEL'), help='''
    Optional, limits for geometry
    ''')
    args = parser.parse_args()
    main(args)

