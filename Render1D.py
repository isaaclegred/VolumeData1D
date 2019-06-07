# Distribute≈çd under the MIT License.
# See LICENSE.txt for details.
#!/usr/bin/env python
#Python script to render 1D data written using SpECTRE in format v2
# This script originated from someone in Summer of 2018.  The format for volume
# data files has changed and we can use as a model the GenerateXdmf.py in spectre/tools
# as a model.  In addition we probably want to make this script compatible with both
# h5py and the python wrappers of SpECTRE H5 functions.  To this end we may want to factor
# even more functions out


import glob
import h5py
import argparse
import sys
import os # Gives the script additional functionality but may be unnesecary
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
try:
    import Tkinter
except ImportError:
    import tkinter as Tkinter

global line
global title
# May Want these to be arrays, may not matter but should see if performance will be
# a big deal.
time = []
coords = []
data = []


def find_extrema_over_data_set(arr):

    '''
    Find max and min over a range of number arrays
    :param arr: the array over which to find the max and min
    This doesn't really work if there are nan valued data pts.
    '''
    # The last statment of the docstring may or may not be true

    return np.nanmin(np.asarray(arr)), np.nanmax(np.asarray(arr))


def init():

    '''
    Initialize the animation canvas
    :return: empty line and title info
    '''

    line.set_data([], [])
    title.set_text("")
    return line, title


def animate(iteration):
    '''
    Update the animation canvas
    '''

    title.set_text("t = %.5f" % time[iteration])
    line.set_data(coords[iteration], data[iteration])
    return line, title


def parse_cmd_line():
    '''
    parse command-line arguments
    :return: dictionary of the command-line args, dashes are underscores
    '''

    parser = argparse.ArgumentParser(description='Render 1-dimensional data',
                                     formatter_class=
                                     argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--file-prefix', type=str, required=True,
                        help='common prefix of all h5 files being used \
                        in the case of a single h5 file, it is the file name \
                        without the .h5 extension')
    parser.add_argument('--var', type=str, required=True,
                        help='name of variable to render. eg \'psi\', \
                        \'psi-Error\' or \'psi-Analytic\'')
    parser.add_argument('--time', type=int,required=False,
                        help='if given renders the integer observation step \
                        instead of an animation (optional)')
    parser.add_argument('--save', type=str, required=False,
                        help='set to the name of the output file you want \
                        written. For animations this saves an mp4 file and \
                        for stills a pdf. (optional)')
    parser.add_argument('--fps', type=str, required=False,
                        help='Set the number of frames per second when writing\
                        an animation to disk.(optional)')
    parser.add_argument('--interval', type=str, required=False,
                        help='number of milliseconds (optional)')
    parser.add_argument('--list-vars', type=bool, required=False,
                        help='if true then write list of vars in h5 file \
                        and exit (optional)')
    return vars(parser.parse_args())

def get_h5_files(file_prefix):
    '''
    Get a list of the h5 files containing the data
    :return list of h5 files containing volume data
    '''
    h5_file_names = glob.glob("*.h5")
    h5_files = [h5py.File(file_name, 'r')
                   for file_name in h5_file_names]
    return(h5_files)

def print_var_names(args):
    # This will need to be changed to be consistent with .vol files.
    '''
    Print all available variables to screen
    :param args:
    :return: None
    '''
    file_prefix = args["file-prefix"]
    h5files = get_h5_files(file_prefix)
    volfile = h5files[0]["element_data.vol"]
    obs_id_0  = volfile.keys()[0]
    grid_names = volfile[Observation_Id_0].keys()
    grid = volfile[Observation_Id_0][grid_names[0]]
    variables = grid.keys()
    variables.remove("connectivity")
    variables.remove("x-coord")
    print("Variables in H5 file:\n[%s]" % ', '.join(map(str, variables)))
    return None


def get_data(args):
    # This probably will need to be changed in order to
    # be consitent with the current format of the .vol files.
    '''
    Get the data to be plotted
    #:return: the array of data, coords, and time
    '''
    file_prefix = args["file-prefix"]
    var_name = args["var"]
    h5files = get_h5_files(file_prefix)
    volfiles =  [h5file['element_data.vol'] for h5file in h5files]
    # Get a list of times from the first vol file
    ids_times = [(obs_id,obs_id.attrs['observation_value']) for obs_id in volfiles[0].keys()]
    ids_times.sort(key = lambda pair: pair[1])
    time_data = {}
    for id_and_time in ids_times:
        time_data[id_and_time] = []
        for volfile in volfiles:
            Obs_Id_File  = volfile[id_and_time[0]]
            local_data = []
            local_coords = []
            for grid_name in Obs_Id_File.keys():
                h5_grid = h5_time[grid_name]
                local_data += list(h5_grid[var_name])
                local_coords += list(h5_grid['InertialCoordinates_x']))
            local_coords_and_data  = zip(local_coords, local_data)
            time_data[id_and_time] += local_coords_and_data
        time_data[id_and_time].sort(key = lambda pair: pair[0])
        time.append(time)
        coords.append([pair[0] for pair in time_data[id_and_time]])
        data.append([pair[1] for pair in time_data[id_and_time]])

    return None


def render_single_time(args):

    '''
    Renders a single time snap shot
    :param args: the command line arguments
    :return: None
    '''

    plt.xlabel("x")
    plt.ylabel(args['var'])
    plt.title("t = %.5f" % time[int(args['time'])])
    plt.plot(coords[int(args['time'])],
             data[int(args['time'])], 'o')
    if args['save']:
        print("Writing still to file %s.pdf" % args['save'])
        plt.savefig("%s.pdf" % args['save'], transparent=True,
                    format='pdf', bbox_inches='tight')
    else:
        plt.show()
    return None


def render_animation(args):

    '''
    Render an animation of the data
    :param args: the command line arguments
    :return: None
    '''
    # These things are mostly fine probably, just clean up and
    # See if anything can be made more efficient
    fig = plt.figure()
    ax = plt.axes(xlim=(find_extrema_over_data_set(coords)),
                  ylim=(find_extrema_over_data_set(data)))
    global line
    global title
    line, = ax.plot([], [], 'o', lw=2)
    ax.set_xlabel('x')
    ax.set_ylabel(args['var'])
    title = ax.set_title("")
    my_interval = 200
    if args['interval']:
        my_interval = float(args['interval'])
    anim = animation.FuncAnimation(fig, animate, init_func=init,
                                   frames=len(time), interval=my_interval)
    if args['save']:
        myfps = 30
        if args['fps']:
            myfps = int(args['fps'])
        print("Writing animation to file %s.mp4 at %d frames per second" %
              (args['save'], myfps))
        anim.save("%s.mp4" % args['save'], fps=myfps,
                  extra_args=['-vcodec', 'libx264'])
    else:
        def propagate_exceptions(self, exc, val, tb):
            raise exc(val).with_traceback(tb)
        Tkinter.Tk.report_callback_exception = propagate_exceptions
        plt.show()
    return None


def main(args):
    '''
    :param args: command line arguments
    :return: None
    '''

    if args['list_vars']:
        print_var_names(args)
        sys.exit(0)

    get_data(args)
    if args['time']:
        render_single_time(args)
    else:
        render_animation(args)
    return None

if __name__ == "__main__":
    try:
        main(parse_cmd_line())
    except KeyboardInterrupt:
        pass
