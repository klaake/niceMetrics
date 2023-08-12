from nicegui import ui

ui.html('''
    <style>
    .cell-fail { background-color: #f6695e; }
    .cell-pass { background-color: #70bf73; }
   </style>
''')

grid = ui.aggrid({
    'columnDefs': [
        {'headerName': 'Name', 'field': 'name'},
        {'headerName': 'Age', 'field': 'age'},
    ],
    'rowData': [
        {'name': 'Alice', 'age': 18},
        {'name': 'Bob', 'age': 21},
        {'name': 'Carol', 'age': 42},
    ],
})

async def format() -> None:
    await ui.run_javascript(f'''
        getElement({grid.id}).gridOptions.columnApi.getColumn("age").getColDef().cellClassRules = {{
            "cell-fail": x => x.value < 21,
            "cell-pass": x => x.value >= 21,
        }};
        getElement({grid.id}).gridOptions.api.refreshCells();
    ''', respond=False)

ui.timer(0, format, once=True)

ui.run()