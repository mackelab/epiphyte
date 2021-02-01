print("Epiphyte launch-raster version loaded.")

import pandas as pd
import matplotlib.pyplot as plt
import holoviews as hv
from holoviews import opts
from holoviews import streams
import panel as pn
import param
from datetime import datetime
from holoviews.operation import decimate
from bokeh.models import HoverTool
# use Bokeh as the underlying plotting library
hv.extension('bokeh')
import sys
import os
# import everything database related
from database.db_setup import *


##############################################
# Setting formatting and plotting parameters #
##############################################

# set parameters for patient IDs and session numbers of experiment sessions
patients = config.patients
sessions = config.sessions
patient_ids = []
for patient in patients:
    patient_ids.append(patient['patient_id'])
# TODO session number hard coded so far. Needs to be dynamically adapted to selected patient ID
session_nrs = [1]

# Set default parameters for initial plotting
default_patient_id = 1
default_session_nr = 1

# define which regions should be able to highlight
# keep in mind that each option has to be implemented further below
# highlights = ["None", "Pause", "Continuous Watch"]
highlights = ["None", "Pauses", "Skips"]


# instantiate the input text boxes where information can be added to enable uploading data to the database
input_name = pn.widgets.TextInput(name="Name of Annotation", placeholder="Enter a name for the annotation")
input_annotator_id = pn.widgets.TextInput(name="Annotator ID", placeholder="Enter your annotator ID (e.g. 'p1')")
input_additional_info = pn.widgets.TextInput(name="Additional Information", placeholder="Optional additional information...")

# instantiate the box edit tool
boxes = hv.Rectangles([])
box_stream = streams.BoxEdit(source=boxes, num_objects=100, styles={'fill_color': ['red']})
boxes.opts(
    opts.Rectangles(active_tools=['box_edit'], fill_alpha=0.5))
# define and activate hover tool for box edits, so the index of the box is shown, when the mouse is hovering over boxes
hover = HoverTool(tooltips=[
    ("index", "$index"),
])
boxes.opts(tools=[hover])


#################################
# Fxns for making static raster #
#################################

def get_patient_session_info():
    
    # set parameters for patient IDs and session numbers of experiment sessions
    patients = config.patients
    sessions = config.sessions
    patient_ids = []
    for patient in patients:
        patient_ids.append(patient['patient_id'])
    # TODO session number hard coded so far. Needs to be dynamically adapted to selected patient ID
    session_nrs = [1]
    
    return patient_ids, session_nrs
 
def make_static_raster(reset_timescale=False):
    # TODO modify to allow for multiple sessions for a single patient  
    """
    Creates the static rasterplots for each patient and saves in the directory ../visualization/images/.
    
    This function first checks if the static images have already been generated and saved locally. If not, 
    will generate ones for any patients that have been added since last run. 
    """
    
    patient_ids, session_ids = get_patient_session_info()
    print("Patient ids: {}".format(patient_ids))
    print("Sessions: {}".format(session_ids))
    # check for existing image file; create if not present
    
    save_dir = "{}/visualization/images/".format(config.PATH_TO_REPO)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    # for the list of patients in the database, check for existing static rasterplots
    for patient in patient_ids:
        session_id = session_ids[0]
        
        # if not reset_timescale:
        #     pat_filename = os.path.join(save_dir, "raster_plot_{}".format(patient))
        
        if reset_timescale:
            pat_filename = os.path.join(save_dir, "raster_plot_{}_rescaled".format(patient))
        else:
            pat_filename = os.path.join(save_dir, "raster_plot_{}".format(patient))

        if os.path.exists("{}.png".format(pat_filename)):
            print("Static raster exists for patient {}. Skipping to next.".format(patient))
            continue
        
        print("Generating static raster for patient {}...".format(patient))
        # for any patients without a static plot, generate one    
        
        rectime = get_neural_rectime_of_patient(patient, session_id)
        rec_start = rectime[0]
        rec_stop = rectime[-1]
        
        all_data = get_spikes_from_patient_session(patient, session_id) # this might not work yet
        
        fig = plt.figure(figsize=(80,30))
        ax1 = fig.add_subplot(121)
        ax1.eventplot(all_data, linewidths=0.1, linelengths=1.2)
        
        ratio = 0.3
        xleft, xright = ax1.get_xlim()
        ybottom, ytop = ax1.get_ylim()
        
        ax1.set_aspect(abs((xright-xleft)/(ybottom-ytop))*ratio)
        ax1.set_yticks([])
        #ax1.xaxis.set_tick_params(labelsize=30)
        ax1.tick_params(axis='x', labelsize=15 )
        
        plt.title('Spikes, Patient {}'.format(patient), size=25)
        plt.xlabel('Time in neural recording system scale (msec)', size=20)
        plt.ylabel('Units', size=20)
    
        ax1.spines['left'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['top'].set_visible(False)
        
        plt.tight_layout()

        # save the newly generated plot
        plt.savefig(pat_filename, bbox_inches="tight")
        #plt.savefig(save + "{}_raster.svg".format(self.pat_id), bbox_inches="tight")
        
        print("Raster saved.")
        
        ## only for troubleshooting
        # plt.show()

        
###############################
# Interactive raster functions #
###############################

class RasterPlot(param.Parameterized):
    """
    This class creates the raster plot and the corresponding menu to select the patient ID and the session number
    """
    patient_id = param.ObjectSelector(default=default_patient_id, objects=patient_ids)
    session_nr = param.ObjectSelector(default=default_session_nr, objects=session_nrs)
    highlight = param.ObjectSelector(default="None", objects=highlights)

    @param.depends('patient_id', 'session_nr', 'highlight')
    def load_raster(self):
        nr_units = get_number_of_units_for_patient(self.patient_id)
        neural_rec_time = get_neural_rectime_of_patient(self.patient_id, self.session_nr) / 1000
        data_array = []
        for i in range(nr_units):
            spikes = get_spiking_activity(self.patient_id, self.session_nr, i)
            # delete downloaded file from working directory
            if os.path.exists("neural_rec_time.npy"):
                os.remove("neural_rec_time.npy")
            data_array.append(list(np.array(spikes) - neural_rec_time[0]))

        ret = []
        for i in range(len(data_array)):
            # i is unit ID
            for j in data_array[i]:
                # j is spike time
                ret.append((j, i))

        scatter = hv.Scatter(ret)

        # Toggle variable decimate_plot to specify whether you'd like to use decimate
        # Decimate only plots a maximum number of elements at each zoom step, this way the plot is much faster
        # If decimate is not activated, the plot is clean, but very slow
        decimate_plot = True
        if decimate_plot:
            scatter = scatter.opts(color='blue', marker='dash', size=12, alpha=1, line_width=0.6, angle=90,
                                   xlabel='Time from beginning of recording in milliseconds', ylabel='Unit ID')
            # adjust the max_samples parameter if the plot is too slow or if you think it can handle even more spikes
            raster = decimate(scatter, max_samples=40000).opts(width=1500, height=800) * boxes
        else:
            scatter = scatter.opts(color='blue', marker='dash', size=12, alpha=1, line_width=0.2, angle=90)
            raster = scatter.opts(width=1500, height=800, xlabel='Time from beginning of recording in milliseconds', ylabel='Unit ID') * boxes

        # extracting necessary information from the database
        start_times_pauses = \
        (MoviePauses() & "patient_id={}".format(self.patient_id) & "session_nr={}".format(self.session_nr)).fetch(
            "start_times")[0]
        stop_times_pauses = \
        (MoviePauses() & "patient_id={}".format(self.patient_id) & "session_nr={}".format(self.session_nr)).fetch(
            "stop_times")[0]
        start_times_pauses = start_times_pauses - neural_rec_time[0]
        stop_times_pauses = stop_times_pauses - neural_rec_time[0]

        start_times_skips = \
        (MovieSkips() & "patient_id={}".format(self.patient_id) & "session_nr={}".format(self.session_nr)).fetch("start_times")[0]
        stop_times_skips = \
        (MovieSkips() & "patient_id={}".format(self.patient_id) & "session_nr={}".format(self.session_nr)).fetch("stop_times")[0]
        start_times_skips = start_times_skips - neural_rec_time[0]
        stop_times_skips = stop_times_skips - neural_rec_time[0]

        # The user can select a region which should be highlighted on top of the raster plot.
        # Here every option of the highlights variable from above has to be implemented
        if self.highlight == "Pauses":
            ov = hv.NdOverlay(
                {i: hv.VSpan(start_times_pauses[i], stop_times_pauses[i]).opts(color='orange', alpha=0.4) for i in range(len(start_times_pauses))})
            
        if self.highlight == "Skips":
            ov = hv.NdOverlay(
                {i: hv.VSpan(start_times_skips[i], stop_times_skips[i]).opts(color='green', alpha=0.4) for i in range(len(start_times_skips))})
            
        if self.highlight == 'None':
            ov = hv.NdOverlay({i: hv.VSpan(0, 0).opts(color='white', alpha=0) for i in range(1)})

        return raster * ov.opts(framewise=True)


class StaticRasterPlot(param.Parameterized):
    """
    This class creates the raster plot and the corresponding menu to select the patient ID and the session number
    """
    patient_id = param.ObjectSelector(default=default_patient_id, objects=patient_ids)
    session_nr = param.ObjectSelector(default=default_session_nr, objects=session_nrs)

    @param.depends('patient_id', 'session_nr')
    def load_raster(self):
        name_plot = "{}/visualization/images/raster_plot_{}".format(config.PATH_TO_REPO, self.patient_id)

        return pn.panel("{}.png".format(name_plot))


class ShowCoords(param.Parameterized):
    """
    This class displays the coordinates of selected boxes.
    """

    # instantiating the action button, which will then trigger updating the output
    action = param.Action(lambda x: x.param.trigger('action'), label='Show Selected Data Ranges')

    @param.depends('action')
    def display_all_data(self):
        if not box_stream.data is None:
            nr_boxes = len(box_stream.data['x0'])
            list_boxes = ["Box {}".format(i) for i in range(nr_boxes)]
            df = pd.DataFrame({
                'Boxes': list_boxes,
                'x0 - earlier time stamp': box_stream.data['x0'],
                'x1 - later time stamp': box_stream.data['x1'],
                'y0 - lower unit': np.round(np.array(box_stream.data['y0'])),
                'y1 - upper unit': np.round(np.array(box_stream.data['y1']))})
            return hv.Table(df)
        return None


class AddingToDB(param.Parameterized):
    """
    Adding data to the database by clicking the action button.
    """

    # instantiating the action button which will trigger uploading the data to the database
    add_to_db = param.Action(lambda x: x.param.trigger('add_to_db'), label='Add Selected Ranges to Data Base')

    @param.depends('add_to_db')
    def add_data_to_database(self):
        if not input_name.value == '' and not input_annotator_id.value == '':

            now = datetime.now()
            t = now.strftime("%Y-%m-%d")

            try:
                ManualAnnotation.insert1({'patient_id': p.patient_id, "annotator_id": input_annotator_id.value,
                                   'session_nr': p.session_nr, "label_entry_date": t,
                                   "x_zero": np.array(box_stream.data['x0']),
                                   'x_one': np.array(box_stream.data['x1']), "y_zero": np.array(box_stream.data['y0']),
                                   "y_one": np.array(box_stream.data['y1']), 'name': input_name.value,
                                   "additional_information": input_additional_info.value},
                                  skip_duplicates=True)
                return "## Data added to database"
            except:
                s = "## Uploading to database didn't work."
                e = sys.exc_info()[0]
                return s + str(e)
        else:
            return "Please fill in all text boxes."


# instantiating the raster plot
p = RasterPlot()
