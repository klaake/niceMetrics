from nicegui import ui
from indicator_controller import indicator_controller
from indicator import indicator_commands
import pandas as pd

controller = indicator_controller()
controller.find_indicators(r"C:\Users\kevin\NiceMetrics\data")
controller._readIndicator("apr")
controller._readIndicator("timing")

# This would come from the entry in the view file, which I need to still code...
args = indicator_commands()
args.name = "My Custom Indicator"
args.type = "table"
#args.indicators = ["apr", "timing"]
args.indicators = ["apr"]
#args.join = ["block", "tag"]
#args.table_columns = ["block", "tag", "opens", "shorts", "wns", "tns", "failing_paths"]
args.table_columns = ["block", "tag", "opens", "shorts"]
ind = controller.make_indicator(args)

# make a chart now...
args = indicator_commands()
args.name = "My Custom Chart"
args.type = "line"
args.indicators = ["apr"]
args.plot = ["opens","shorts"]
args.x_axis = "date"
ind = controller.make_indicator(args)
with ui.grid(columns=3) as mygrid:
    mygrid.style("min-height: 33vh; min-width: 75em")
    controller.renderIndicator("My Custom Chart", 3)
    controller.renderIndicator("My Custom Indicator")
    controller.renderIndicator("My Custom Indicator",2)

ui.run()



#ui.icon('thumb_up')
#ui.markdown('This is **Markdown**.')
#ui.html('This is <strong>HTML</strong>.')
#with ui.row():
#    ui.input(label='Data Path', placeholder='directory/file', on_change)
#ui.link('NiceGUI on GitHub', 'https://github.com/zauberzeug/nicegui')
#
#ui.run()
#ui.button('Say hi!', on_click=lambda: ui.notify('Hi!', closeBtn='OK'))

#ui.run()
