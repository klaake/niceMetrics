#!/apps/oss/python-3.11.5/bin/python3

from nicegui import ui, app
from uuid import uuid4
import argparse
import sys
import os

script_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f"{script_directory}/niceMetrics_modules")

from indicator_controller import indicator_controller

parser = argparse.ArgumentParser(description='niceMetrics Options')
parser.add_argument("-native", action="store_true", help='Run in native mode (i.e. local window instead of webhost)', default=False)
parser.add_argument("-title", action="store", help='Title of the browser tab', default="Nice Metrics")
parser.add_argument("-port", action="store", help='Title of the browser tab', default=8080)

parsed_args, unparsed_pargs = parser.parse_known_args()



@ui.page('/niceMetrics')
async def private_indicator_page():
    controller = indicator_controller()
    controller.prepareIndicators()
    controller.displayIndicators()

@ui.page('/niceMetrics/{command}')
async def private_indicator_page_load_data(command: str, data: str, view:str="",filter:str="" ):
    controller = indicator_controller(data_source=data, view_file=view, global_filter=filter)
    controller.findIndicators(data)
    if os.path.exists(view):
        controller.readViewFile(view)

    controller.prepareIndicators()
    controller.displayIndicators()

#@ui.page('/niceMetrics')
#async def main_page():
#    header = ui.header(elevated=True).style('background-color: #3874c8').classes('items-center justify-between')
#    #left_panel = ui.left_drawer(top_corner=False, bottom_corner=True).style('background-color: #d7e3f4; width: 300px;')
#
#    with header:
#        ui.label("Welcome to NiceMetrics!").style("font-size: 200%").tailwind.font_weight('extrabold')
#    #with left_panel:
#    #    ui.link('New Indicator Instance', private_indicator_page, new_tab=True)

metric_arguements = {}

if parsed_args.native is True:
    metric_arguements['native'] = True
if parsed_args.title is not None:
    metric_arguements['title'] = parsed_args.title
if parsed_args.port is not None:
    metric_arguements['port'] = int(parsed_args.port)

#if parsed_args.native is not True:
#    app.on_connect(main_page)
##else:
#    app.on_connect(private_indicator_page)

ui.run(**metric_arguements)
