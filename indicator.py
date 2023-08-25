import pandas as pd
from collections import defaultdict
from functools import reduce
from nicegui import ui
import plotly.express as px
import plotly.graph_objects as go

class indicator_view:
    def __init__(self):
        # This dictionary stores all the files that have been read in, and contains
        # a pointe to their pandas dataframe
        self.indicator_dataframes = defaultdict(lambda: None)

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

    def aggrid(self):
        dataframe=self.display_dataframe
        column_for_ui = []
        for col in self.plot:
            col_rename = self.getRename(col)
            col_data = {'headerName': col_rename, 'field': col, 'sortable' : "true", 
                        'cellClassRules' : self.aggrid_thresholds[col],
                        }


            column_for_ui.append(col_data)
        rows = dataframe.to_dict('records')
        #print(rows)
        with ui.element():
            if self.name is not None:
                ui.label(self.name)
            table =  ui.aggrid({
                'columnDefs':column_for_ui, 
                'rowData':rows, 
                'pagination':'true',
                'paginationAutoPageSize':'true',
                "suppressFieldDotNotation" : "true",
                }).classes(f"col-span-{self.colspan}")

        #for row in table.options['rowData']:
        #    for col, value in row.items():
        #        row[col] = '<a href=https://google.com>' + str(value) + "</a>"
        #    
        table.on('cellClicked', self.onCellClicked)

    def onCellClicked(sender, msg):
        print(sender)
        print(msg)
            
    def line(self, container=None):
        #print(f" X = {self.graph_x}")
        fig = px.line(self.display_dataframe, x=self.graph_x, y=self.plot)
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
            my_chart = ui.plotly(fig).classes(f"col-span-{self.colspan} w-full h-80").style("min-height: 500px")
            radio.mychart = my_chart
            radio.container = container

    def on_chart_change(self, value):
        # Clear out the old chart
        value.sender.container.clear()

        # Render the chart that the user now wants...
        if value.sender.value == "bar":
            self.bar(value.sender.container)
        if value.sender.value == "line":
            self.line(value.sender.container)

    def bar(self, container=None):
        #print(f" X = {self.graph_x}")
        fig = px.bar(self.display_dataframe, x=self.graph_x, y=self.plot)
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
                radio = ui.radio(["line", "bar"], value="bar", on_change=self.on_chart_change).props("inline")
            my_chart = ui.plotly(fig).classes(f"col-span-{self.colspan} w-full h-80").style("min-height: 500px")
            radio.mychart = my_chart
            radio.container = container
        
                



            
            

            
