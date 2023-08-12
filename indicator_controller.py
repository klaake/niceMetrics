import os
import sys
from indicator import indicator_view
import pandas as pd
from collections import defaultdict
import glob
import time
from nicegui import ui
import numpy as np
from matplotlib import pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import re as re


class indicator_controller:
    def __init__(self):
        # Key: Indicator Name, Value = a pandas dataframe
        self.indicator_frames = defaultdict(lambda: None)
        # Key: Indicator Name, Value = list of files that were read in for that particular indicator
        self.indicator_files = defaultdict(lambda: [])
        # This keeps track and tells me if an indicator file has been read
        self.indicator_file_read = defaultdict(lambda: False)
        # Indicator Objects by Name
        self.indicators = defaultdict(lambda: None)
        
        self.MainTitle = None

        self.data_source = None
        self.view_file = None
        self.indicator_header = None
        self.main_title_label = None
        self.mygrid = None

    # This function will search the underlying directories and look for CSV files
    def findIndicators(self, datapath: str) -> bool:
        # Does the directory exist?
        #print(f"Datapath = {datapath}")
        if os.path.exists(datapath) is False:
            return False
        
        # Is it actually a directory?
        if os.path.isdir(datapath) is False:
            return False

        csv_files = glob.glob(f"{datapath}/**/*.csv", recursive=True)

        for file in csv_files:
            file_basename = os.path.basename(file)
            indicator_name = os.path.splitext(file_basename)[0]
            self.indicator_files[indicator_name].append(file)
            #print(f"Storing Indicator ({indicator_name}): {file}")

    def displayIndicators(self):
        # Go through the grid of indicators, and write them out!
        
        if self.indicator_header is not None:
            self.indicator_header.clear()
        else:
            self.indicator_header = ui.header(elevated=True).style('background-color: #3874c8').classes('items-center justify-between')

        if self.mygrid is not None:
            self.mygrid.clear()
        else:
            self.mygrid = ui.grid(columns=3)

        with self.indicator_header:
            with ui.column():
                if self.MainTitle is not None:
                    self.main_title_label = ui.label(self.MainTitle).style('font-size: 200%; font-weight: 300')
                with ui.expansion("Expand Data Input", icon='work', value=True).classes('w-full').style("width:800px") as self.expander:
                    ui.input(label="Data Source Directory").bind_value(self, "data_source").props("outlined dense stack-label").style("width:800px")
                    ui.input(label="Indicator View File").bind_value(self, "view_file").props("outlined dense stack-label").style("width:800px")
                ui.button('Load Indicators', on_click=lambda: self.reload_indicators())

        with self.mygrid:
            self.mygrid.style("min-height: 33vh; min-width: 75em; max-height: 33%")
            for row in self.page_matrix:
                for indicator in row:
                    if indicator is None:
                        #ui.label("spacer")
                        ui.label("")
                        continue
                    if indicator == "colspan":
                        continue

                    ################################################################
                    # Table Indicator!
                    ################################################################
                    if indicator.type == "table":
                        indicator.table()
                    if indicator.type == "line":
                        indicator.line()
                    if indicator.type == "bar":
                        indicator.bar()
                        
    def reload_indicators(self):

        if self.data_source is None:
            ui.notify('ERROR: Data Source is Empty!')
            return
        if self.view_file is None:
            ui.notify('ERROR: View File was Not specified!')
            return
        if not os.path.exists(self.data_source):
            ui.notify(f"ERROR: Data Source Does not exist!")
            ui.notify(self.data_source)
            return
        if not os.path.exists(self.view_file):
            ui.notify(f"ERROR: View File Does Not Exist:")
            ui.notify(self.view_file)
            return
        #self.mygrid.clear()
        #self.indicator_header = None
        #print("RELOADING!")
        self.indicators = defaultdict(lambda: None)
        self.findIndicators(self.data_source)
        self.readViewFile(self.view_file)
        self.prepareIndicators()
        self.displayIndicators()
        
        
    def renderIndicator(self, name, colspan=1):
        indicator = self.indicators[name]
        if indicator is None:
            return False
        
        if indicator.type == "table":
            dataframe = indicator.display_dataframe
            column_for_ui = []
            for col in dataframe.columns:
                col_data = {'name': col, 'label': col, 'field': col, 'sortable' : True, 'align': "left"}
                column_for_ui.append(col_data)

            rows = dataframe.to_dict('records')
            #print(rows)
            with ui.table(
                columns=column_for_ui, 
                rows=rows, 
                pagination=10, 
                title=indicator.name
                ).props('dense').classes(f"col-span-{colspan}") as table:
                self.table = table
        if indicator.type == "line":
            if indicator.joined_dataframe is None:
                dataframe = indicator.display_dataframe
            else:
                dataframe = indicator.get_table_frame()
            fig = px.line(dataframe, x=indicator.graph_x, y=indicator.plot)
            fig.update_layout(title=indicator.name)
            ui.plotly(fig).classes(f"col-span-{colspan}").style("min-height: 300px")

                
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

                    print("Indicator Command:")
                    print(f" Command Type = {indicator_command}")
                    print(f" Command Name = {name}")
                    print(f" Command Data = {indicator_command_data}")

                if indicator_command == "MainTitle":
                    self.MainTitle = indicator_command_data
                    #print(f" Setting Main Title to {self.MainTitle}")
                    continue
                if indicator_command == "Indicator":
                    if self.indicators[name] is None:
                        self.indicators[name] = indicator_view()
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

                    print(f"Type = '{type}'")
                    print(f"Value = '{value}'")
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
                        print("HERE")
                        print(f" Value = {value}, Indicator={indicator}")
                        match = re.search("(\w+)\((.+?)\)", value)
                        if match:
                            indicator = match.groups()[0]
                            column = match.groups()[1]
                            self.indicators[name].graph_x = f"{column}.{indicator}"
                        continue
                                    


            
# This is where I can test the class.....
if __name__ in {"__main__", "__mp_main__"}:

    # Makea new controller object.
    controller = indicator_controller()
    controller.prepareIndicators()
    controller.displayIndicators()
    ui.run(title="Nice Metrics", dark=False, native=True)

    
    



