#!/bin/sh
"export" "DIR=$(dirname $0)"
"exec" "$DIR/venv/bin/python3" "$0" "$@"

from nicegui import ui, app
from indicator_controller import indicator_controller
from uuid import uuid4
import argparse

parser = argparse.ArgumentParser(description='niceMetrics Options')
parser.add_argument("-native", action="store_true", help='Run in native mode (i.e. local window instead of webhost)', default=False)
parser.add_argument("-title", action="store", help='Title of the browser tab', default="Nice Metrics")

parsed_args, unparsed_pargs = parser.parse_known_args()



@ui.page('/niceMetrics/indicator')
async def private_indicator_page():
    controller = indicator_controller()
    controller.prepareIndicators()
    controller.displayIndicators()

@ui.page('/niceMetrics')
async def main_page():
    header = ui.header(elevated=True).style('background-color: #3874c8').classes('items-center justify-between')
    left_panel = ui.left_drawer(top_corner=False, bottom_corner=True).style('background-color: #d7e3f4; width: 300px;')

    with header:
        ui.label("Welcome to NiceMetrics!").style("font-size: 200%").tailwind.font_weight('extrabold')
    with left_panel:
        ui.link('New Indicator Instance', private_indicator_page, new_tab=True)

metric_arguements = {}

if parsed_args.native is True:
    metric_arguements['native'] = True
if parsed_args.title is not None:
    metric_arguements['title'] = parsed_args.title

if parsed_args.native is not True:
    app.on_connect(main_page)
else:
    app.on_connect(private_indicator_page)

ui.run(**metric_arguements)
main_page()