import os
import sys
from indicator import indicator_view, indicator_commands
import pandas as pd
from collections import defaultdict
import glob
import time
from nicegui import ui
import numpy as np
from matplotlib import pyplot as plt
import plotly.graph_objects as go
import plotly.express as px


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

    # This function will search the underlying directories and look for CSV files
    def find_indicators(self, datapath: str) -> bool:
        # Does the directory exist?
        print(f"Datapath = {datapath}")
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
            print(f"Storing Indicator ({indicator_name}): {file}")

    def make_indicator(self, indicator_commands):
        new_indicator = indicator_view()

        for indicator_name in indicator_commands.indicators:
            if self.indicator_frames[indicator_name] is not None:
                new_indicator.add_data(self.indicator_frames[indicator_name])

        if len(indicator_commands.join) > 0:
            new_indicator.merge_data(indicator_commands.join) 

        new_indicator.table_columns = indicator_commands.table_columns
        new_indicator.name = indicator_commands.name
        new_indicator.type = indicator_commands.type
        new_indicator.graph_x = indicator_commands.x_axis
        new_indicator.plot = indicator_commands.plot

        # Store the indicator based on it's name
        self.indicators[new_indicator.name] = new_indicator
        return new_indicator

    def renderIndicator(self, name, colspan=1):
        indicator = self.indicators[name]
        if indicator is None:
            return False
        
        if indicator.type == "table":
            dataframe = indicator.get_table_frame()
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
                dataframe = indicator.get_table_frame('apr')
            else:
                dataframe = indicator.get_table_frame()
            fig = px.line(dataframe, x=indicator.graph_x, y=indicator.plot)
            fig.update_layout(title=indicator.name)
            ui.plotly(fig).classes(f"col-span-{colspan}").style("min-height: 300px")

                
    # This function will take all the indicator files named "indicator" and will
    #  read them into a pandas dataframe.  It will then store that dataframe in the 
    #  self.indicator_frames dictionary
    def _readIndicator(self, indicator_name: str) -> bool:
        # Make sure we have files for this indicator
        if indicator_name not in self.indicator_files:
            return False
        
        for csv_file in self.indicator_files[indicator_name]:
            # Don't read in files that have already been read.
            if self.indicator_file_read[csv_file] is True:
                print(f"Indicator File has already been read: {csv_file}")
                continue

            print(f"Reading in Indicator File = {csv_file}")
            new_df = pd.read_csv(csv_file)

            if self.indicator_frames[indicator_name] is not None:
                combined_dataframe = pd.concat([self.indicator_frames[indicator_name], new_df], ignore_index=True, sort=False)
                # Do I need to remove the old frame?
                del self.indicator_frames[indicator_name] 
                # Store the new frame...
                self.indicator_frames[indicator_name] = combined_dataframe 
            else:
                self.indicator_frames[indicator_name] = new_df

            # Remove any duplicate data.
            print("Dropping Dups...")
            self.indicator_frames[indicator_name] = self.indicator_frames[indicator_name].drop_duplicates()
            # Reset the index since I might have removed some data.
            self.indicator_frames[indicator_name] = self.indicator_frames[indicator_name].reset_index(drop=True)
            self.indicator_frames[indicator_name].name = indicator_name
        #print(self.indicator_frames[indicator_name])

            
# This is where I can test the class.....
if __name__ == "__main__":

    controller = indicator_controller()
    controller.find_indicators(r"C:\Users\kevin\NiceMetrics\data")
    controller._readIndicator("apr")
    controller._readIndicator("timing")

    # This would come from the entry in the view file, which I need to still code...
    args = indicator_commands()
    args.name = "My Custom Indicator"
    args.type = "table"
    args.indicators = ["apr", "timing"]
    args.join = ["block", "tag"]
    args.table_columns = ["block", "date", "opens", "shorts", "wns", "tns", "failing_paths"]
    controller.make_indicator(args)
    input("Press Enter to exit...")
    



