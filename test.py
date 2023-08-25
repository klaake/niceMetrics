#from nicegui import ui
#
#
##rows = [{'block.timing': 'myblockA', 'tag.timing': 'run1', 'wns.timing': -500, 'tns.timing': -100000, 'failing_paths.timing': 5000}, {'block.timing': 'myblockA', 'tag.timing': 'run2', 'wns.timing': -250, 'tns.timing': -50000, 'failing_paths.timing': 2500}, {'block.timing': 'myblockA', 'tag.timing': 'run3', 'wns.timing': -100, 'tns.timing': -10000, 'failing_paths.timing': 1200}, {'block.timing': 'myblockA', 'tag.timing': 'run4', 'wns.timing': -50, 'tns.timing': -4500, 'failing_paths.timing': 600}, {'block.timing': 'myblockA', 'tag.timing': 'run5', 'wns.timing': -20, 'tns.timing': -1000, 'failing_paths.timing': 200}, {'block.timing': 'myblockA', 'tag.timing': 'run6', 'wns.timing': -5, 'tns.timing': -100, 'failing_paths.timing': 40}, {'block.timing': 'myblockA', 'tag.timing': 'run7', 'wns.timing': -5, 'tns.timing': -100, 'failing_paths.timing': 40}, {'block.timing': 'myblockA', 'tag.timing': 'run8', 'wns.timing': -5, 'tns.timing': -100, 'failing_paths.timing': 40}, {'block.timing': 'myblockA', 'tag.timing': 'run9', 'wns.timing': -5, 'tns.timing': -100, 'failing_paths.timing': 40}, {'block.timing': 'myblockA', 'tag.timing': 'run10', 'wns.timing': -5, 'tns.timing': -100, 'failing_paths.timing': 40}, {'block.timing': 'myblockA', 'tag.timing': 'run11', 'wns.timing': -5, 'tns.timing': -100, 'failing_paths.timing': 20}, {'block.timing': 'myblockA', 'tag.timing': 'run12', 'wns.timing': -5, 'tns.timing': -100, 'failing_paths.timing': 20}, {'block.timing': 'myblockA', 'tag.timing': 'run13', 'wns.timing': -5, 'tns.timing': -100, 'failing_paths.timing': 20}, {'block.timing': 'myblockA', 'tag.timing': 'run14', 'wns.timing': -5, 'tns.timing': -100, 'failing_paths.timing': 0}, {'block.timing': 'myblockA', 'tag.timing': 'run15', 'wns.timing': -5, 'tns.timing': -100, 'failing_paths.timing': 0}]
#rows = [{'block.timing': 'myblockA', 'tag.timing': 'run1', 'wns.timing': -500, 'tns.timing': -100000, 'failing_paths.timing': 5000}]
#
#ui.aggrid({
#    'columnDefs': [
#        {'headerName': 'Block', 'field': 'block.timing', 'sortable': "true"},
#        {'headerName': 'Tag', 'field': 'tag.timing', 'sortable': "true"},
#        {'headerName': 'WNS', 'field': 'wns.timing', 'sortable': "true"},
#        {'headerName': 'TNS', 'field': 'tns.timing', 'sortable': "true"},
#        {'headerName': 'Path Count', 'field': 'failing_paths.timing', 'sortable': "true"},
#    ],
#    'rowData':[{'block.timing': 'myblockA', 'tag.timing': 'run1', 'wns.timing': -500, 'tns.timing': -100000, 'failing_paths.timing': 5000}],
#    "pagination" : "true",
#    "paginationAutoPageSize" : "true",
#}).classes('max-h-300').style("min-height: 33vh")
#
#ui.run()


from nicegui import ui

ui.html("<div>")
ui.label("Test")
ui.aggrid({
    'columnDefs': [
        {'headerName': 'Name', 'field': 'name.foo', 'sortable': "true"},
        {'headerName': 'Age', 'field': 'age.foo', 'sortable': "true"},
    ],
    'rowData': [
        {'name.foo': 'Alice', 'age.foo': 18},
        {'name.foo': 'Bob', 'age.foo': 21},
        {'name.foo': 'Carol', 'age.foo': 42},
    ],
    "pagination" : "true",
    "paginationAutoPageSize" : "true",
    "suppressFieldDotNotation" : "true"
}).classes('max-h-300').style("min-height: 33vh")
ui.html("</div>")

ui.run(native=True)