import pandas as pd
from collections import defaultdict
from functools import reduce

class indicator_commands:
    def __init__(self):
        self.name = "Unknown"
        self.type = "table"
        self.indicators = []
        self.join = []
        self.table_columns = []
        self.plot = []
        self.x_axis = ""
        self.rowspan = 1
        self.colspan = 1
    
class indicator_view:
    def __init__(self):
        # This dictionary stores all the files that have been read in, and contains
        # a pointe to their pandas dataframe
        self.indicator_dataframes = defaultdict(lambda: None)
        self.joined_dataframe = None

        # Default indicator type is a table.
        self.type = 'table'

        # If a table, store the columns
        self.table_columns = []

        # if a graph, store the x and y values
        self.graph_x = ""
        self.graph_y = ""

        self.plot = []

    def add_data(self, dataframe):
        # Get the name of the dataframe...
        indicator_name = dataframe.name
        self.indicator_dataframes[indicator_name] = dataframe
    
    def get_table_frame(self, name=None):
        if name is None:
            filtered_dataframe = self.joined_dataframe[self.table_columns]
            return filtered_dataframe
        else:
            return self.indicator_dataframes[name]

    def merge_data(self, merge_columns):
        if isinstance(merge_columns,list) is not True:
            return None

        frames_to_merge = []
        combined_dataframe = None

        for name in self.indicator_dataframes.keys():
            df = self.indicator_dataframes[name]
            frames_to_merge.append(df)

        if len(frames_to_merge) > 1:
            combined_dataframe = reduce(lambda left, right: pd.merge(left, right, on=merge_columns, suffixes=("." + left.name, "." + right.name)), frames_to_merge)

        print(combined_dataframe)
        self.joined_dataframe = combined_dataframe



            
            

            
