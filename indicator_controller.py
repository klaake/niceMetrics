import os
import sys
import pandas as pd
from collections import defaultdict
from functools import reduce
import glob
import time
from nicegui import ui, Tailwind
import numpy as np
from matplotlib import pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import re as re
from urllib.parse import quote
from functools import partial


class indicator_controller:
    def __init__(self, data_source=None, view_file=None, global_filter=None):
        # Key: Indicator Name, Value = a pandas dataframe
        self.indicator_frames = defaultdict(lambda: None)
        # Key: Indicator Name, Value = list of files that were read in for that particular indicator
        self.indicator_files = defaultdict(lambda: [])
        # This keeps track and tells me if an indicator file has been read
        self.indicator_file_read = defaultdict(lambda: False)
        # Indicator Objects by Name
        self.indicators = defaultdict(lambda: None)
        
        # This is the title that will appear at the top of the page.
        self.MainTitle = None

        # The directory to start looking for CSV files for the indicators.  Set by an 
        # input box
        self.data_source = data_source
        # The view file that describes how to setup the page
        self.view_file = view_file

        # This is a global filter string that will apply to everything being plotted...
        self.global_filter_string = global_filter
        self.global_filters = []
        if self.global_filter_string:
            self.global_filters = self.makeDataFilter(self.global_filter_string)

        # This is a ui.header() object that will store the input boxes and load indicator
        # button
        self.indicator_header = None

        # This is the ui.grid() object that sets up the 3xN grid of indicator objects.
        self.mygrid = None

        # This is the minimum size a widget can be on the screen. Can configure in the view file
        self.min_height = "500px"

        # This is how fast the indicator will self-refresh.  Off by default
        self.refresh_interval = 60
        self.refresh_enabled = False

    def makeDataFilter(self, filter_string):
        filters = []
        if filter_string:
            filter_segments = filter_string.split('&')
            #print(filter_segments)
            for seg in filter_segments:
                match = re.search("^(\S+?)(!*~|!*=|>=*|<=*)(.+)", seg)
                if match:
                    column_name = match.groups()[0]
                    operation = match.groups()[1]
                    value = match.groups()[2]
                    new_filter = defaultdict(lambda: None)
                    new_filter['column'] = column_name
                    new_filter['operation'] = operation
                    new_filter['value'] = value
                    filters.append(new_filter)
        return filters

    # This function will search the underlying directories and look for CSV files
    def findIndicators(self, datapath: str) -> bool:
        # Does the directory exist?
        if os.path.exists(datapath) is False:
            return False
        
        # Is it actually a directory?
        if os.path.isdir(datapath) is False:
            return False

        # Get the CSV files via a glob command.  Look for anything ending in .csv
        csv_files = glob.glob(f"{datapath}/**/*.csv", recursive=True)

        for file in csv_files:
            # the indicator name should be the name in <indicator>.csv
            file_basename = os.path.basename(file)
            indicator_name = os.path.splitext(file_basename)[0]
            # Store the files we found by the indicator name.
            self.indicator_files[indicator_name].append(file)

    def displayIndicators(self):
        # Go through the grid of indicators, and write them out!

        # either create the header, or clear it out depending on if we're refreshing or creating initially
        if self.indicator_header is not None:
            self.indicator_header.clear()
        else:
            self.indicator_header = ui.header(elevated=True).style('background-color: #3874c8').classes('items-center justify-between')

        # Same with the grid.  If we're refreshing we clear it out, else we create it
        if self.mygrid is not None:
            self.mygrid.clear()
        else:
            self.mygrid = ui.grid(columns=3)

        # Create the header.  Add 2 input boxes.  One for the data directory and one for the 
        # view file.  Add the ability to hide/show the boxes for more visible room for the 
        # indicators.
        with self.indicator_header:
            with ui.column().classes('w-full'):
                with ui.row().classes('w-full'):
                    with ui.expansion("Hide/Show Data and View Inputs",  value=True).classes('w-full').style("width:800px") as self.expander:
                        ui.input(label="Data Source Directory").bind_value(self, "data_source").props("outlined dense stack-label").style("width:800px")
                        ui.input(label="Indicator View File").bind_value(self, "view_file").props("outlined dense stack-label").style("width:800px")
                        ui.input(label="Global Filter").bind_value(self, "global_filter_string").props("outlined dense stack-label").style("width:800px")
                    with ui.link('', 'http://your_help_link.html',True).classes('ml-auto').style('color: inherit;'):
                        ui.icon('help').classes('ml-auto text-5xl')
                container = ui.element().classes(f"col-span-3")
                with container:
                    with ui.row():
                            ui.button('Load Indicators', on_click=lambda: self.reload_indicators())
                            ui.switch('Enable Auto-Refresh').on("click", self.refresh_timer).value=self.refresh_enabled
                            self.interval = ui.number("Seconds", placeholder=60)
                            self.interval.on("update:model-value", self.update_timer_value)
                            self.interval.value = self.refresh_interval
                            #self.interval.visible = False
        with self.mygrid:
            if self.MainTitle is not None:
                ui.label(self.MainTitle).classes("text-center col-span-3").style("font-size: 200%").tailwind.font_weight('extrabold')
            #self.mygrid.style("min-height: 33vh; min-width: 75em; max-height: 33%")
            self.mygrid.style("min-height: 33vh; min-width: 100%; max-height: 33%")
            for row in self.page_matrix:
                for indicator in row:
                    if indicator is None:
                        #ui.label("spacer")
                        ui.label("").classes("w-1/3")
                        continue
                    if indicator == "colspan":
                        continue

                    ################################################################
                    # Table Indicator!
                    ################################################################
                    if indicator.type == "table":
                        indicator.aggrid(global_filter=self.global_filters)
                    if indicator.type == "aggrid":
                        indicator.aggrid(global_filter=self.global_filters)
                    if indicator.type == "line":
                        indicator.line(global_filter=self.global_filters)
                    if indicator.type == "bar":
                        indicator.bar(global_filter=self.global_filters)
            ui.label("").classes("w-1/3")
            ui.label("").classes("w-1/3")
            ui.label("").classes("w-1/3")
    
    def update_timer_value(self, value):
        self.refresh_interval = float(value.args)
        try:
            self.timer.interval = self.refresh_interval
        except:
            pass
    
    def refresh_timer(self, value):
        self.refresh_enabled = value.sender.value
        if self.refresh_enabled is True:
            #self.interval.visible = True
            self.timer = ui.timer(self.refresh_interval, self.reload_indicators)
            self.timer.active = True
        else:
            #self.interval.visible = False
            self.timer.active = False
                        
    def reload_indicators(self):

        parameters = defaultdict(lambda: "")
        if self.data_source is not None:
            parameters['data'] = self.data_source
        if self.view_file is not None:
            parameters['view'] = self.view_file
        if self.global_filter_string is not None:
            parameters['filter'] = self.global_filter_string

        encoded_params = {key: quote(str(value)) for key, value in parameters.items()}
        my_url = f"load?data={encoded_params['data']}&&view={encoded_params['view']}&&filter={encoded_params['filter']}"
        ui.open(my_url)
        return
        
    # This function will take all the indicator files named "indicator" and will
    #  read them into a pandas dataframe.  It will then store that dataframe in the 
    #  self.indicator_frames dictionary
    def _readDataIntoFrame(self, indicator_name: str, reread:bool=False):
        # Make sure we have files for this indicator
        if indicator_name not in self.indicator_files:
            #print(f"No Files Matching '{indicator_name}'")
            return None

        if reread is False and self.indicator_frames[indicator_name] is not None:
            #print(f"Returning Pre-Read Data for '{indicator_name}'")
            #print(self.indicator_frames[indicator_name])
            return self.indicator_frames[indicator_name]
        
        for csv_file in self.indicator_files[indicator_name]:
            # Don't read in files that have already been read.
            if self.indicator_file_read[csv_file] is True:
                #print(f"Indicator File has already been read: {csv_file}")
                continue

            #print(f"Reading in Indicator File = {csv_file}")
            new_df = pd.read_csv(csv_file)
            new_df.fillna('',inplace=True)
            # Add a suffix to the end of the indicator indicating what indicator it belongs to.
            for col in new_df.columns:
                new_df.rename(columns={col : col + "." + indicator_name}, inplace=True)

            #print(new_df)

            if self.indicator_frames[indicator_name] is not None:
                combined_dataframe = pd.concat([self.indicator_frames[indicator_name], new_df], ignore_index=True, sort=False)
                # Do I need to remove the old frame?
                del self.indicator_frames[indicator_name] 
                # Store the new frame...
                self.indicator_frames[indicator_name] = combined_dataframe 
            else:
                self.indicator_frames[indicator_name] = new_df
            
            #print("Dataframe:")
            #print(new_df)

            # Remove any duplicate data.
            #print("Dropping Dups...")
            self.indicator_frames[indicator_name] = self.indicator_frames[indicator_name].drop_duplicates()
            # Reset the index since I might have removed some data.
            self.indicator_frames[indicator_name] = self.indicator_frames[indicator_name].reset_index(drop=True)
            self.indicator_frames[indicator_name].name = indicator_name

            #print("FINAL FRAME")
            #print(self.indicator_frames[indicator_name])
        #print(self.indicator_frames[indicator_name])
        return self.indicator_frames[indicator_name]

    def prepareIndicators(self):
        # Now that the view file has been read into the system and indicator_view
        # objects have been made, read in the data we need, and make a matrix of where
        # indicator objects will live.
        max_weight = 0
        if self.indicators:
            for indicator_name in self.indicators.keys():
                #print(f"Processing Indicator = {indicator_name}")
                view = self.indicators[indicator_name]
                for csv_name in view.indicators_to_read:
                    dataframe = self._readDataIntoFrame(csv_name)
                    view.indicator_dataframes[csv_name] = dataframe

                # If I need to combine 2 different data sets into 1 table, then do it here.
                # else, this function will just take the one dataframe and use it
                view.makeDisplayDataframe()

                # Calculate the position 'weight' so I can order the views appropriately
                view.position_weight = (view.pos_row-1)*3 + (view.pos_col-1) 
                #print(f"Indicator Weight = {view.position_weight}")
                if max_weight < view.position_weight:
                    max_weight = view.position_weight
        else:
            # Make an indicator for every data we have
            row = 1
            for ind in self.indicator_files.keys():
                dataframe = self._readDataIntoFrame(ind)
                # Make a new view file
                view = indicator_view(self)
                view.name=ind
                for c in dataframe.columns:
                    view.plot.append(c)
                    view.pos_row = row
                    view.pos_col = 1
                    view.colspan = 3
                    string = ".foo"
                    col_display_name = re.sub(f"\.{ind}$", '', c)
                    view.setRename(c, col_display_name)
                view.type = "aggrid"

                view.indicator_dataframes[ind] = dataframe
                view.display_dataframe = dataframe

                view.position_weight = (view.pos_row-1)*3 + (view.pos_col-1) 
                if max_weight < view.position_weight:
                    max_weight = view.position_weight
                
                self.indicators[ind] = view


        # Now that I have a max weight, calcualte a matrix of indicators.
        matrix_rows = int(max_weight/3) + 1
        #print(f"Total Rows = {matrix_rows}")

        # Initialize the matrix to None
        self.page_matrix = [ [None]*3 for _ in range(matrix_rows)]

        for name, view in sorted(self.indicators.items(), key=lambda item: item[1].position_weight):
            #print(f"VIEW: {name}, weight: {view.position_weight}")
            row = int(view.position_weight/3)
            col = view.position_weight % 3
            #print(f"  ROW:{row}, COL:{col}")
            self.page_matrix[row][col] = view
            if view.colspan > 1:
                for i in range(1,view.colspan):
                    col += 1
                    #print(f"Colspan Col = {col}")
                    if col <= 2:
                        self.page_matrix[row][col] = 'colspan'
                
        #print(self.page_matrix)

    def readViewFile(self, file):
        if os.path.exists(file) is False:
            return
        with open(file, "r") as fh:
            for line in fh:
                # Skip blank lines...
                if line.isspace():
                    continue
                # Skip comments
                if line.lstrip().startswith('#'):
                    continue
                # Remove training whitespace
                line = line.rstrip()

                original_line = line
                result = re.search("^\s*(\w+)\((.*?)\)\:(.+)$", line)
                if result:
                    indicator_command = result.groups()[0]
                    name = result.groups()[1]
                    indicator_command_data = result.groups()[2]

                    #print("Indicator Command:")
                    #print(f" Command Type = {indicator_command}")
                    #print(f" Command Name = {name}")
                    #print(f" Command Data = {indicator_command_data}")

                if indicator_command == "MainTitle":
                    self.MainTitle = indicator_command_data
                    #print(f" Setting Main Title to {self.MainTitle}")
                    continue
                if indicator_command == "MinHeight":
                    self.min_height = indicator_command_data
                    #print(f" Setting Main Title to {self.MainTitle}")
                    continue
                if indicator_command == "Indicator":
                    if self.indicators[name] is None:
                        self.indicators[name] = indicator_view(self)
                        self.indicators[name].name = name

                    # Break the indicator data up by <type>=<value>
                    location_of_equal = indicator_command_data.find('=')
                    if location_of_equal != -1:
                        type = indicator_command_data[:location_of_equal]
                        value = indicator_command_data[location_of_equal+1:]
                    else:
                        #print(f"Could not parse line:")
                        #print(f" {original_line}")
                        continue

                    #print(f"Type = '{type}'")
                    #print(f"Value = '{value}'")
                    ###########################
                    # data command
                    ###########################
                    if type == "data" and value:
                        csvs_to_read = value.split(',')
                        for indicator_name in csvs_to_read:
                            self.indicators[name].indicators_to_read.append(indicator_name)
                        #print("Indicators to Read is now:")
                        #print(self.indicators[name].indicators_to_read)
                        continue
                    ###########################
                    # join command
                    ###########################
                    if type == "join" and value:
                        columns = value.split(',')
                        for c in columns:
                            self.indicators[name].columns_to_join.append(c)
                        continue
                    ###########################
                    # position command
                    ###########################
                    if type == "position" and value:
                        pos = value.split(',')
                        try:
                            self.indicators[name].pos_row = int(pos[0])
                            self.indicators[name].pos_col = int(pos[1])
                        except:
                            print(f"-W- Invalid position specified:")
                            print(f"-W-   {value}")
                            continue
                    ###########################
                    # rowspan command
                    ###########################
                    if type == "rowspan" and value:
                        try:
                            self.indicators[name].rowspan = int(value)
                        except:
                            print(f"-W- Invalid rowspan specified:")
                            print(f"-W-   {value}")
                            continue
                    ###########################
                    # pagesize command
                    ###########################
                    if type == "pagesize" and value:
                        try:
                            self.indicators[name].page_size = int(value)
                        except:
                            print(f"-W- Invalid page size specified:")
                            print(f"-W-   {value}")
                            continue
                    ###########################
                    # colspan command
                    ###########################
                    if type == "colspan" and value:
                        try:
                            self.indicators[name].colspan = int(value)
                        except:
                            print(f"-W- Invalid colspan specified:")
                            print(f"-W-   {value}")
                            continue
                    ###########################
                    # type command
                    ###########################
                    if type == "type" and value:
                        self.indicators[name].type = value
                        continue
                    if type == "sortType" and value:
                        self.indicators[name].sortType = value
                        continue
                    if type == "filter" and value:
                        self.indicators[name].local_filter = self.makeDataFilter(value)
                        continue
                    if type == "sortBy" and value:
                        match=re.match("^(\S+)\((.+?)\)", value)
                        if match:
                            i = match.groups()[0]
                            c = match.groups()[1]
                            self.indicators[name].sortBy = f"{c}.{i}"
                        continue
                    if type == "max_entries" and value:
                        try:
                            self.indicators[name].max_entries = int(value)
                        except:
                            pass
                        continue
                    if type == "threshold" and value:
                        match = re.search("^(\w+)\((.+?)\)(.+?)\,(.+)", value) 
                        if match:
                            ind = match.groups()[0]
                            col = match.groups()[1]
                            condition = match.groups()[2]
                            color = match.groups()[3]
                            #string= f'''
                            #"(col.name=='{col}.{ind}'&col.value{condition})?'bg-{color} text-black' : 'text-black'"'''
                            string= f'''
                            'bg-{color}' : col.name=='{col}.{ind}'&col.value{condition},'''
                            self.indicators[name].thresholds.append(string)

                            self.indicators[name].aggrid_thresholds[f"{col}.{ind}"][f"bg-{color}"] = f"x {condition}"

                            #print("Adding Threshold:")
                            #print(string)
                        continue
                    ###########################
                    # plot command
                    ###########################
                    if type == "plot" and value:
                        while True:
                            match = re.search("(\w+)\((.+?)\)", value)
                            if match:
                                indicator = match.groups()[0]
                                columns = match.groups()[1]
                                for c in columns.split(','):
                                    c = c.rstrip()
                                    c = c.lstrip()
                                    self.indicators[name].plot.append(f"{c}.{indicator}")
                                    self.indicators[name].setRename(f"{c}.{indicator}", c)
                                    #print(f" Adding '{indicator}.{c} to plot list")
                                value = re.sub("(\w+)\((.+?)\)", "", value, 1)
                                #print(f"Value is now '{value}'")
                            else:
                                break
                        continue
                    if type == "xaxis" and value:
                        #print("HERE")
                        #print(f" Value = {value}, Indicator={indicator}")
                        match = re.search("(\w+)\((.+?)\)", value)
                        if match:
                            indicator = match.groups()[0]
                            column = match.groups()[1]
                            self.indicators[name].graph_x = f"{column}.{indicator}"
                        continue
                                    
class indicator_view:
    def __init__(self, controller=None):
        # This dictionary stores all the files that have been read in, and contains
        # a pointe to their pandas dataframe
        self.indicator_dataframes = defaultdict(lambda: None)

        # This is the controller object that made me...
        self.controller = controller

        # Final dataframe
        self.display_dataframe = None

        # Default indicator type is a table.
        self.type = 'table'
        self.name = None

        # if a graph, store the x and y values
        self.graph_x = ""
        self.graph_y = ""

        self.indicators_to_read = []
        self.columns_to_join = []

        # If a table, store the columns, if a chart, this is what I'm charting
        self.plot = []

        self.renames = defaultdict(lambda: None)

        # This is where in the grid the indicator will live
        self.pos_row = 1
        self.pos_col = 1
        self.rowspan = 1
        self.colspan = 1

        # A sortable number so I can place things appropriately
        self.position_weight = None

        # This stores a list of thresholds to apply to tables.
        self.thresholds = []
        self.aggrid_thresholds = defaultdict(lambda: {})

        # This is the max rows displayed for a table before you need to page.
        self.page_size = 10

        self.max_entries = None

        self.sortBy = None
        self.sortType = "descending"

        self.local_filter = []
    
    def setRename(self, old_name:str, new_name:str):
        self.renames[old_name] = new_name

    def getRename(self, name:str):
        rename = name
        while self.renames[rename] is not None:
            rename = self.renames[rename]
        return rename

    def getPlotDataframe(self, name=None):
        #print("Plot Values")
        #print(self.plot)
        filtered_dataframe = self.display_dataframe.loc[:, self.plot]
        #print("DONE")
        return filtered_dataframe

    def makeDisplayDataframe(self):
        #if len(self.columns_to_join) == 0:
        #    self.display_dataframe = self.indicator_dataframes.items()[1]
        #    return

        # Sometimes, the user wants to combine 2 datafranes into a single indicator.
        # keep a list of frames that the user wants to merge
        frames_to_merge = []
        # This is the frame that we're going to display to the user.  It might be a single idnicator, or it 
        # might be a merged indicator of multiple frames.
        self.display_dataframe = None

        # See how many indicators we're read into the class.  Decide how many we're going to merge
        for name in self.indicator_dataframes.keys():
            df = self.indicator_dataframes[name]
            frames_to_merge.append(df)

        #print("COLUMNS TO JOIN")
        # These are the columns we're going to merge together.
        #print(self.columns_to_join)
        
        if len(frames_to_merge) > 1:
            #print("MERGING MORE THAN ONE FRAME")
            #combined_dataframe = reduce(lambda left, right: pd.merge(left, right, on=self.columns_to_join, suffixes=("." + left.name, "." + right.name)), frames_to_merge)
            #self.display_dataframe = reduce(lambda left, right: pd.merge(left, right, on=self.columns_to_join), frames_to_merge)
            for column in self.columns_to_join:
                self.display_dataframe = reduce(lambda left, right: pd.merge(left, right, left_on=column+"."+left.name, right_on=column+"."+right.name), frames_to_merge)
        else:
            self.display_dataframe = frames_to_merge[0]

        # Add suffixes to the non-joined columns that don't already have suffixes
        #for name in self.indicator_dataframes.keys():
        #    df = self.indicator_dataframes[name]
        #    for column in df.columns:
        #        if column in self.display_dataframe and column not in self.columns_to_join:
        #            self.display_dataframe.rename(columns={column : column + "." + name}, inplace=True)
        #print(self.display_dataframe)

        # Sort the dataframe if the user wants it
        if self.sortBy is not None:
            #print(f"Sorting by '{self.sortBy}'")
            if self.sortType != "ascending":
                self.display_dataframe.sort_values(by=self.sortBy, ascending=False, inplace=True)
            else:
                self.display_dataframe.sort_values(by=self.sortBy, ascending=True, inplace=True)
            #print(self.display_dataframe)


    def table(self):
        dataframe=self.display_dataframe
        column_for_ui = []
        for col in self.plot:
            col_rename = self.getRename(col)
            col_data = {'name': col, 'label': col_rename, 'field': col, 'sortable' : True, 'align': "left"}
            column_for_ui.append(col_data)
        rows = dataframe.to_dict('records')
        with ui.table(
            columns=column_for_ui, 
            rows=rows, 
            pagination=self.page_size,
            title=self.name,
            ).props('dense').classes(f"col-span-{self.colspan} my-sticky-header-table") as table:
            self.table = table

            if len(self.thresholds) > 0:
            # This is how do you coloring of cells conditionally
                slot_command = '''
                    <q-tr :props="props">
                        <q-td 
                            v-for="col in props.cols"
                            :key="col.name"
                            :props="props"
                            :class="{'''
                            
                for cmd in self.thresholds:
                    slot_command = slot_command + cmd

                slot_command += r'''}"
                        >
                            {{ col.value }}
                        </q-td>
                    </q-tr>
                '''
                #print("SLOT COMMAND:")
                #print(slot_command)
                table.add_slot('body', slot_command)
                table.on('cellClicked', self.onCellClicked)

    def filter_dataframe(self, dataframe, global_filter:list=None, local_filter:list=None, max_entries:int=None):
        if global_filter:
            new_frame = dataframe
            for flt in global_filter:
                #print(flt)
                matching_columns = new_frame.filter(like=f"{flt['column']}.", axis = 1)
                for c in matching_columns:
                    if flt['operation'] == "~":
                        new_frame = new_frame[new_frame[c].str.contains(flt['value'], regex=True)]
                    if flt['operation'] == "!~":
                        new_frame = new_frame[~new_frame[c].str.contains(flt['value'], regex=True)]
                    if flt['operation'] == "=":
                        new_frame = new_frame[new_frame[c] == flt['value']]
                    if flt['operation'] == "!=":
                        new_frame = new_frame[new_frame[c] != flt['value']]
                    if flt['operation'] == ">":
                        new_frame = new_frame[new_frame[c] > flt['value']]
                    if flt['operation'] == ">=":
                        new_frame = new_frame[new_frame[c] >= flt['value']]
                    if flt['operation'] == "<":
                        new_frame = new_frame[new_frame[c] < flt['value']]
                    if flt['operation'] == "<=":
                        new_frame = new_frame[new_frame[c] < flt['value']]
            dataframe=new_frame
        if local_filter:
            new_frame = dataframe
            for flt in local_filter:
                #print(flt)
                matching_columns = new_frame.filter(like=f"{flt['column']}.", axis = 1)
                for c in matching_columns:
                    if flt['operation'] == "~":
                        new_frame = new_frame[new_frame[c].str.contains(flt['value'], regex=True)]
                    if flt['operation'] == "!~":
                        new_frame = new_frame[~new_frame[c].str.contains(flt['value'], regex=True)]
                        #print(new_frame)
                    if flt['operation'] == "=":
                        new_frame = new_frame[new_frame[c] == flt['value']]
                    if flt['operation'] == "!=":
                        new_frame = new_frame[new_frame[c] != flt['value']]
                    if flt['operation'] == ">":
                        new_frame = new_frame[new_frame[c] > flt['value']]
                    if flt['operation'] == ">=":
                        new_frame = new_frame[new_frame[c] >= flt['value']]
                    if flt['operation'] == "<":
                        new_frame = new_frame[new_frame[c] < flt['value']]
                    if flt['operation'] == "<=":
                        new_frame = new_frame[new_frame[c] < flt['value']]

            dataframe=new_frame

        if max_entries is not None:
            new_frame = dataframe.tail(max_entries)
            dataframe = new_frame

        return dataframe

    def aggrid(self, global_filter:list=None):

        dataframe = self.filter_dataframe(self.display_dataframe, global_filter, self.local_filter, max_entries=self.max_entries)

        column_for_ui = []
        for col in self.plot:
            col_rename = self.getRename(col)
            col_data = {'headerName': col_rename, 'field': col, 'sortable' : "true", 
                        'cellClassRules' : self.aggrid_thresholds[col],
                        }


            column_for_ui.append(col_data)
        rows = dataframe.to_dict('records')
        #print(rows)
        with ui.element().classes(f"col-span-{self.colspan}"):
            with ui.element():
                with ui.row():
                    if self.name is not None:
                        ui.label(self.name).style("font-size: 20px; font-weight: bold;")
                    with ui.element().classes('ml-auto'):
                        btn = ui.button('Export To CSV')
                        btn.style("font-size: 10px; padding: 6px 10px; float: right")
                        btn.classes('ml-auto')
                        btn2 = ui.button('Size To Contents')
                        btn2.style("font-size: 10px; padding: 6px 10px; float: right")
                        btn2.classes('ml-auto')
            table =  ui.aggrid({
                'columnDefs':column_for_ui, 
                'rowData':rows, 
                'pagination':'true',
                'defaultColDef' : { 'autoHeaderHeight' : 'true', 'wrapHeaderText' : 'true', 'resizable' : 'true' },
                #'paginationAutoPageSize':'true',
                "suppressFieldDotNotation" : "true",
                }).classes(f"col-span-{self.colspan}").style(f"min-height: {self.controller.min_height}")
            btn.on("click", lambda: table.call_api_method('exportDataAsCsv'))
            btn2.on("click", lambda: table.call_column_api_method('autoSizeAllColumns'))

        #for row in table.options['rowData']:
        #    for col, value in row.items():
        #        row[col] = '<a href=https://google.com>' + str(value) + "</a>"
        #    
        table.on('cellClicked', self.onCellClicked)
        table.on('gridReady', self.sizeToContents)
        self.mytable = table

    def onCellClicked(sender, msg):
        file = None
        column_clicked = msg.args['colId']
        indicator_name = column_clicked.split('.')[1]
        column_name = column_clicked.split('.')[0]
        try:
            file = msg.args['data'][f"metadata.{indicator_name}"]
        except:
            pass

        if file is not None:
            if os.path.exists(file):
                text = indicator_view.getMetaData(file,column_name)
                
                with ui.dialog().classes('w-full') as dialog, ui.card().classes('w-full'):
                    ui.textarea(f"{indicator_name} : {column_clicked}", value=text).classes('w-full')
                dialog.open()

    def sizeToContents(sender):
        sender.mytable.call_column_api_method('autoSizeAllColumns')
            
    def line(self, global_filter:list=None, container=None):
        dataframe = self.filter_dataframe(self.display_dataframe, global_filter, self.local_filter, max_entries=self.max_entries)
        #print(f" X = {self.graph_x}")
        #fig = px.line(self.display_dataframe, x=self.graph_x, y=self.plot)
        #print(dataframe)
        fig = px.line(dataframe, x=self.graph_x, y=self.plot)
        fig.update_layout(title=self.name)
        fig.update_layout(legend=dict(
           orientation="h",
           yanchor="bottom",
           y=1.02,
           xanchor="right", 
           x=1
        ))

        if container is None:
            container = ui.element().classes(f"col-span-{self.colspan}")
            
        with container:
            with ui.row():
                ui.label("Change Graph Type:")
                radio = ui.radio(["line", "bar"], value="line", on_change=self.on_chart_change).props("inline")
            my_chart = ui.plotly(fig).classes(f"col-span-{self.colspan} w-full h-80").style(f"min-height: {self.controller.min_height}")
            radio.mychart = my_chart
            radio.container = container


    def bar(self, global_filter:list=None, container=None):
        #print(f" X = {self.graph_x}")
        dataframe = self.filter_dataframe(self.display_dataframe, global_filter, self.local_filter, max_entries=self.max_entries)
        fig = px.bar(dataframe, x=self.graph_x, y=self.plot)
        fig.update_layout(title=self.name)
        fig.update_layout(legend=dict(
           orientation="h",
           yanchor="bottom",
           y=1.02,
           xanchor="right", 
           x=1
        ))

        # Put all of this stuff into a constainer.  This way, I can "clear" the container and switch from a 
        # line graph to a bar graph, etc, and I can lump in things like labels or any other stuff and have it 
        # all stay in it's grid position
        if container is None:
            container = ui.element().classes(f"col-span-{self.colspan}")

        with container:
            with ui.row():
                ui.label("Change Graph Type:")
                radio = ui.radio(["line", "bar"], value="bar", on_change=self.on_chart_change).props("inline")
            my_chart = ui.plotly(fig).classes(f"col-span-{self.colspan} w-full h-80").style(f"min-height: {self.controller.min_height}")
            radio.mychart = my_chart
            radio.container = container

    def on_chart_change(self, value):
        # Clear out the old chart
        value.sender.container.clear()

        # Render the chart that the user now wants...
        if value.sender.value == "bar":
            self.bar(container=value.sender.container)
        if value.sender.value == "line":
            self.line(container=value.sender.container)
    
    def getMetaData(file, type):
        in_metadata = False
        result = []
        with open(file, "r") as fh:
            for line in fh:
                # Skip blank lines...
                if line.isspace():
                    continue
                if line.startswith(f"#META({type})"):
                    in_metadata = True
                    continue
                if line.startswith('#META('):
                    in_metadata = False
                    continue
                if in_metadata:
                    result.append(line)
        return "".join(result)
                    
            
# This is where I can test the class.....
if __name__ in {"__main__", "__mp_main__"}:

    # Makea new controller object.
    controller = indicator_controller()
    controller.data_source = "/Users/kevinlaake/projects/niceMetrics"
    controller.view_file = "/Users/kevinlaake/projects/niceMetrics/sample_view"
    controller.prepareIndicators()
    controller.displayIndicators()
    ui.run(title="Nice Metrics", dark=False)

    
    



